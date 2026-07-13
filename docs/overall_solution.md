# 整体赛题方案

## 1. 总体目标

构建一个面向 NutShell Cache 的 UCAgent 辅助验证环境，使其具备以下能力：

- 可复现：同一 seed、同一配置下结果稳定。
- 可扩展：DUT-independent core 与 Toffee/Picker 绑定层解耦。
- 可检错：scoreboard 能发现读数据、mask、writeback、响应顺序等典型问题。
- 可量化：功能覆盖率有明确 bins 和回归报告。
- 可答辩：保留设计文档、验收文档、bug 记录和 AI 协作记录。

## 2. 架构设计

验证环境分为四层：

| 层级 | 职责 | 当前状态 |
| --- | --- | --- |
| DUT 集成层 | Picker 生成仿真模型，Toffee 驱动 clock/reset/信号 | 边界已保留，待真实 DUT 信号 |
| 协议适配层 | 把 DUT 信号转换成统一事务 `CacheTxn`/`CacheResponse` | 核心数据结构已完成 |
| 验证核心层 | generator、reference model、memory agent、scoreboard、coverage、fault injection | 已完成并通过测试 |
| 回归报告层 | pytest、core regression CLI、coverage/bug/report 输出 | 已完成 core 级闭环 |

## 3. 核心组件

### 3.1 Transaction Model

`CacheTxn` 描述 CPU 侧事务：

- `op`: read/write。
- `addr`: byte address。
- `size`: 1/2/4/8。
- `data`: write data。
- `mask`: byte mask。
- `txn_id`: 顺序或接口 ID。
- `uncached`: uncached/MMIO 场景。

`CacheResponse` 描述响应和可观测副作用：

- read data。
- hit/miss。
- dirty eviction。
- writeback address/data。
- error。

### 3.2 Reference Model

参考模型使用 byte-addressable memory 和 set/way/tag cache model：

- miss 时从 memory 拉取整条 line。
- write 按 byte mask merge。
- 每个 set 维护 LRU 顺序。
- dirty victim eviction 时写回整条 line。
- uncached 事务直接访问 memory。

### 3.3 Generator

激励包括：

- Smoke：基础 read/write。
- Directed：partial write、same-set replacement、dirty eviction、clean eviction。
- CRV：地址、大小、mask、读写类型、uncached 按权重随机。
- Stress：可扩展为高 miss rate、连续请求、长 latency。

### 3.4 Scoreboard

scoreboard 按事务顺序比较：

- transaction id。
- read data。
- error。
- dirty eviction 标记。
- writeback address/data。

当前 core 级测试已经证明 scoreboard 可检出：

- read corruption。
- partial write mask drop。
- dirty writeback corruption。
- response order swap。

### 3.5 Coverage

required bins 包括：

- op：read/write。
- size：1/2/4/8。
- access：read hit/miss、write hit/miss。
- replacement：clean/dirty。
- mask：full/single/sparse。
- address：same set、line boundary。
- latency：short/long。

当前 directed closure 达到 `19/19`，即 core required bins `100%`。

### 3.6 Memory Agent

`ScriptedMemoryAgent` 是协议无关的 memory-side 模型：

- 支持 read/write 请求。
- 支持 byte mask write。
- 支持固定或单次指定 latency。
- 支持 ready/backpressure pattern。
- 支持 drain 到 idle。

真实 DUT 接入时，Toffee adapter 只需要把 memory-side DUT 信号翻译成 `MemoryRequest`，再把 `MemoryResponse` 驱回 DUT。

## 4. 当前执行结果

WSL2 执行命令：

```bash
cd /mnt/d/UCagent
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests
PYTHONPATH=src .venv/bin/python -m cache_vip.regression --seeds 1,2,3 --count 200 --report-dir reports
```

结果：

| 项目 | 结果 |
| --- | --- |
| compileall | PASS |
| pytest | 77 portable tests passed（以最新 CI 为准） |
| core regression | PASS, 3 seeds x 300 txns |
| required core coverage | 100%, 19/19 |
| fault detection | 5/5 detected |

## 5. 真实 DUT 接入方案

1. 使用 Picker 生成 NutShell Cache Python 仿真模型。
2. 根据生成模型更新 `configs/signal_map.yaml`。
3. 在 `ToffeeCacheAdapter` 中实现 reset、drive request、sample response。
4. 若 memory 侧由 testbench 提供，增加 memory agent，支持 fill、writeback、latency、backpressure。
5. 先跑 smoke，再跑 directed，最后跑 CRV 多 seed。
6. 将真实 RTL 结果补入 `reports/coverage_summary.md` 和 `docs/verification_report.md`。

## 6. 风险与应对

| 风险 | 应对 |
| --- | --- |
| DUT 信号名和假设接口不一致 | 通过 `signal_map.yaml` 隔离适配 |
| Cache policy 和参考模型不一致 | 将 replacement/write-allocate policy 参数化 |
| memory 侧响应支持乱序 | 增加 txn id/source id 匹配队列 |
| coverage 只覆盖 core，未覆盖 RTL | 接入 Toffee monitor 后导出 DUT 实测 coverage |
| AI 生成代码遗漏 corner case | 保留人工 review、负向测试和 bug tracker |

## 7. 项目规则

### 7.1 验证环境要求

**所有测试验证必须在 WSL2 环境中完成**：

| 项目 | 要求 |
| --- | --- |
| 操作系统 | Ubuntu on WSL2 |
| 项目路径 | `/mnt/d/UCagent` |
| Python | 3.14.4（使用项目 `.venv`） |
| 虚拟环境 | 必须使用项目根目录下的 `.venv` |
| 依赖安装 | `pip install -e .`（editable install） |

### 7.2 验证命令规范

所有测试必须通过以下命令在 WSL2 中执行：

```bash
cd /mnt/d/UCagent
source .venv/bin/activate
python -m compileall src tests
python -m pytest tests
```

### 7.3 回归命令

```bash
PYTHONPATH=src python -m cache_vip.regression --seeds 1,2,3 --count 300 --report-dir reports
```

### 7.4 结果记录

- 测试结果必须记录在 `reports/` 目录下
- 真实 RTL 验证结果必须更新到 `reports/coverage_summary.md` 和 `docs/verification_report.md`
- 失败用例必须保留最小复现序列和波形路径
