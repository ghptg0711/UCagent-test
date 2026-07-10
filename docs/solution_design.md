# 基于 UCAgent 的 NutShell Cache 自动化验证方案

## 1. 目标与提交物

目标是构建一个可复现、可扩展、能体现人工深度定制的 Cache 验证环境，覆盖 NutShell Cache 的读写命中、缺失填充、替换、写回、掩码写、回压、乱序/延迟内存响应和一致性相关风险点。

提交物规划：

- 代码仓库：`src/`、`tests/`、`configs/`、`docs/`、`reports/`，根目录包含 Apache 2.0 `LICENSE`。
- 验证组件：Cache 事务模型、CPU 侧 Agent、Memory 侧 Agent、参考模型、Scoreboard、Coverage、Fault Injection。
- 激励发生器：基础随机、约束随机、定向 corner case、压力测试 profile。
- 验证报告：测试计划、覆盖率分析、Bug 追踪、AI 生成与人工修正对照表。

当前完成状态：

- DUT 无关验证核心已实现：事务模型、参考模型、激励生成器、scoreboard、coverage、fault injection。
- WSL2 本地验证已通过：`compileall` 成功，`pytest` 共 12 个用例全通过，core regression CLI 通过。
- Toffee/Picker 绑定层保留在 `src/cache_vip/toffee_adapter.py`，待接入真实 NutShell Cache Picker 输出后补齐具体信号访问。

## 2. 总体架构

验证环境分为四层：

1. DUT 集成层：Picker 生成仿真模型，Toffee 负责时钟、复位、信号访问和协程调度。
2. 协议适配层：把 NutShell Cache 的 CPU 请求/响应、内存请求/响应信号转换成统一的 `CacheTxn` 和 `MemTxn`。
3. 验证核心层：Generator、Driver、Monitor、Reference Model、Scoreboard、Coverage。
4. 回归与报告层：pytest/Toffee regression、coverage dump、bug log、AI 协同记录。

当前仓库先实现第三层的 DUT 无关核心，随后根据你本地 WSL2 中的实际信号名补齐 Toffee 绑定层。

## 3. 验证对象假设

在没有直接读取本地 NutShell Cache RTL 的前提下，先按典型 L1 DCache 风险建模：

- 支持字节/半字/字/双字读写，按 byte mask 生效。
- Cache line 大小可配置，默认 64B。
- set/way 可配置，默认 64 sets、4 ways。
- miss 后向下级 memory 发起 line fill。
- dirty line 被替换时必须写回。
- 支持 valid、dirty、tag、data、replacement state。
- 内存侧可能产生 wait、backpressure、variable latency。

绑定真实 DUT 后，需要用 `configs/signal_map.yaml` 固化具体接口：CPU 侧是否为 SRAM-like、AXI-like、TileLink-like，内存侧是否具备 source/id、opcode、mask、beat 等字段。

## 4. Generator 设计

激励分为五类：

- Smoke：少量顺序读写，验证环境能闭环。
- Directed：同 line 多 size/mask 写、跨 set 冲突、替换写回、读后写、写后读。
- CRV：地址、size、mask、data、stride、cacheability、burst length、stall pattern 按权重随机。
- Stress：高 miss rate、同 set 多 way+1 冲突、dirty eviction、内存长延迟、CPU 连续 back-to-back 请求。
- Fault Injection：内存返回数据翻转、写回丢 byte、响应延迟极端化、模拟替换状态错误，用于证明 scoreboard 能检出。

人工深度定制重点：

- 构造 `ways + 1` 同 set 不同 tag 的替换序列，强制触发 victim 选择与 dirty writeback。
- 构造 partial write merge：同一 line 内不同 mask 多次写入，再全 line 读取比对。
- 构造 alias 地址：相同 index 不同 tag、相邻 line、边界地址、非对齐访问。
- 构造 replay/backpressure：CPU 请求密集发出，memory response 随机延迟。

## 5. Scoreboard 与参考模型

Scoreboard 采用 cycle-insensitive 的事务级比对：

- CPU 请求进入参考模型，得到期望响应。
- Monitor 捕获 DUT 响应后按事务 id 或提交顺序匹配。
- 对 read data、write ack、exception/error、memory side effect 逐项检查。
- 参考模型记录 cache line valid/dirty/tag/data 和 LRU 状态。
- 对 dirty eviction 写回地址和数据进行检查。

若 DUT 接口不暴露 memory writeback，可通过下级 memory model 的观测口捕获。

参考模型实现要点：

- `ByteMemory` 作为下级内存黄金模型，按 byte 保存状态，天然支持 mask merge。
- `ReferenceCache` 按 set/way/tag 建模，miss 时从 `ByteMemory` 拉取整条 line。
- LRU 使用每个 set 一条 MRU 到 LRU 的 way 序列，命中和分配后更新。
- dirty victim 替换时写回整条 line，并在 `CacheResponse.writeback_addr/writeback_data` 中暴露给 scoreboard。
- uncached 事务直接访问 `ByteMemory`，不污染 cache line。

## 6. Coverage 设计

功能覆盖率目标不低于 90%，基础 bin 包括：

- op：read、write。
- size：1B、2B、4B、8B。
- hit/miss：read hit、read miss、write hit、write miss。
- replacement：clean eviction、dirty eviction、all ways occupied。
- mask：full mask、single byte、sparse mask。
- address：same line、same set different tag、line boundary、uncached/MMIO。
- latency：zero/short/long memory delay。
- backpressure：CPU stall、memory stall。
- cross：op x hit/miss、size x mask、replacement x dirty。

## 7. Bug 注入与可检出性

至少保留以下故障注入实验：

- Read data corruption：memory 返回或 DUT 响应某 bit 翻转，scoreboard 必须报错。
- Partial write mask bug：随机丢弃一个 byte mask，后续 read 必须发现数据不一致。
- Dirty writeback bug：evict dirty line 时写回数据被破坏，后续重新读取必须发现。
- Replacement bug：固定选择 way0 或错误更新 LRU，定向替换序列必须暴露。
- Response ordering bug：在不支持乱序的接口上调换两个响应，scoreboard 必须报错。

已落地的 core 级负向测试：

- `test_scoreboard_detects_read_corruption`：读响应 bit flip 可检出。
- `test_scoreboard_detects_partial_write_mask_drop`：partial write 丢 mask 后，后续 read mismatch 可检出。
- `test_scoreboard_detects_dirty_writeback_corruption`：dirty eviction 写回数据破坏可检出。
- `test_scoreboard_detects_response_order_swap`：响应顺序调换可检出。

## 8. UCAgent 协同策略

建议在报告中明确记录：

- AI 生成：初始 Toffee harness、基础 Driver/Monitor、基础随机 Generator、报告初稿。
- 人工修正：协议信号映射、复杂 CRV 约束、替换/写回参考模型、coverage cross、fault injection、code review。
- Prompt 策略：先让 UCAgent 生成局部组件，再人工制定接口边界和验收标准；对 corner case 使用表格化 prompt 限定输入输出。
- 盲区记录：AI 容易忽略 byte mask merge、dirty eviction、memory latency、响应顺序和 cacheability 边界。

## 9. 执行里程碑

1. M0：仓库结构、许可证、设计文档、验收计划。状态：完成。
2. M1：事务模型、Generator、Reference Model、Scoreboard、Coverage 单测通过。状态：完成。
3. M2：Toffee/Picker DUT 接入，smoke case 闭环。状态：待真实 DUT 信号映射。
4. M3：directed corner case 和 CRV regression 达到稳定运行。状态：core directed 已完成，DUT regression 待接入。
5. M4：fault injection case 证明可检出。状态：core 级 4 类 fault 已完成。
6. M5：覆盖率大于 90%，生成最终验证报告。状态：core required bins 达到 100%，DUT functional coverage 待实测。

## 10. 当前测试证据

WSL2 执行目录：`/mnt/d/UCagent`。

```bash
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests
PYTHONPATH=src .venv/bin/python -m cache_vip.regression --seeds 1,2,3 --count 300 --report-dir reports
```

结果：

- `compileall`：通过。
- `pytest`：68 passed。
- `core regression`：PASS，required bins 19/19，fault detection 5/5。
- `test_directed_stream_reaches_required_core_coverage`：core required functional bins 达到 100%。

## 11. 真实 DUT 接入步骤

1. 用 Picker 为 NutShell Cache 生成 Python 可加载仿真模型。
2. 根据 Picker 输出和 RTL 端口更新 `configs/signal_map.example.yaml`，另存为本地 `configs/signal_map.yaml`。
3. 在 `ToffeeCacheAdapter` 中完成 reset、CPU request drive、CPU response sample。
4. 如果 memory 侧由 testbench 提供，增加 memory agent，把 fill、writeback 和 backpressure 接入同一个 `Scoreboard`。
5. 先跑 smoke case，再跑 directed sequence，最后跑多 seed CRV regression。
6. 将 DUT 实测覆盖率、失败 seed、波形路径和 bug 修复记录补入 `reports/`。
