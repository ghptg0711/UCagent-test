# AI 缺陷与人工修正对比表

> 本表是赛题评分维度二.1(协同过程记录)的核心证据,系统记录 UCAgent 生成代码中的缺陷/盲区,以及人工如何通过直接改写或指令微调(Prompt Tuning)修正。一等奖评审明确要求"详尽的 AI 缺陷与人工修正对比表"。
>
> 配套文档:`reports/ai_collaboration_log.md`(逐轮记录)、`reports/bug_tracker.md`(缺陷追踪表)、`reports/ai_collaboration_log.md` "Prompt Tuning Case Studies" 章节。

## 一、总览

| 维度 | AI 生成 | 人工修正 |
| --- | --- | --- |
| 文件数 | 15+ 文件由 UCAgent 生成初版 | 全部文件经人工 review/重构 |
| 缺陷总数 | 11 个记录缺陷 + 3 类能力边界 | 逐一修正或绕过 |
| RTL 设计缺陷 | UCAgent 无法分析 | 人工定位 BUG-010/011 |
| 当前可移植测试 | — | 77 passed；core coverage 100%；Real DUT coverage 待重跑；故障 5/5 经 ScoreboardMismatch 检出 |

## 二、逐模块对比表

| # | 模块 | AI 生成内容 | AI 缺陷 / 盲区 | 人工修正方式 | 证据 |
| --- | --- | --- | --- | --- | --- |
| 1 | 参考模型 `reference_model.py` | 初始 LRU + 字节寻址框架 | LRU 排序逻辑错误(未按 recency);缺 dirty bit 跟踪;缺 writeback 机制 | 直接改写:重写 LRU recency 维护;补 dirty 位;补 dirty eviction writeback 到 memory | Round 1 |
| 2 | Scoreboard `scoreboard.py` | 基础比较框架 | **循环论证**:`_run_stream` 把 `ref.access(txn)` 与自身比较,无法检出任何故障 | 直接改写:跟踪 WRITE 数据,READ 时用独立 oracle 校验;加 writeback 字段比较 | BUG-002, Round 7 P1 |
| 3 | Scoreboard 比较字段 | 只比较 read data | 未比较 hit/miss、dirty eviction、writeback addr/data、error | 直接改写:逐字段加比较检查 | BUG-002, Round 7 P1 |
| 4 | Scoreboard 覆盖率采样 | `evicted_clean` 误算:`(not dirty and not hit)` 把 miss-fill 当成 clean eviction | 直接改写:加 `evicted` 字段,改为 `(evicted and not dirty)` | Round 7 P0 |
| 5 | ToffeeCacheAdapter `toffee_adapter.py` | CPU resp ready 握手框架 | docstring 写"Pull ready high"但代码漏写 `ready.write(1)` | 直接改写:补 `ready.write(1)→wait→write(0)` | BUG-004 |
| 6 | RealDUTWrapper `real_dut_adapter.py` | reset 包装 | `reset_wrapper.write()` 未 `await`,协程从未执行,reset 实际未生效 | 直接改写:补 `await` | BUG-005 |
| 7 | 回归逻辑 `regression.py` | CRV 流 READ 值校验 | 用 `written` dict 校验 READ,未跟踪 eviction,refill 后假阳性 | 直接改写:加 `verify_read_data` 参数,CRV 关闭值校验(仅确定性+覆盖率) | BUG-009 |
| 8 | 回归报告 `regression_analysis.py` | `_format_markdown` | enhanced summary 键名不同,`KeyError` | 直接改写:拆分 `_format_core_markdown` / `_format_enhanced_markdown` | BUG-006 |
| 9 | 回归 DUT 模式 | `dut_seeds` 参数 | 参数声明但从未使用,`dut_regression` 恒空 | 直接改写:补 DUT seed 循环 | BUG-008 |
| 10 | Memory Agent `memory_agent.py` | line size | 硬编码 `64` 字节 | 直接改写:参数化 `line_bytes` | BUG-007 |
| 11 | Coverage `coverage.py` | line_bytes | boundary bin 用字面量 `64` | 直接改写:加 `line_bytes` 参数 | Round 7 P0 |
| 12 | Mock DUT `tests/mock_dut.py` | set_entry 字典 | **无限 way**(永不驱逐),与真实 Cache 行为不符 | 直接改写:实现 way 限制 + LRU 驱逐 + dirty writeback + memory fill | Round 7 P0 |
| 13 | 测试断言 `tests/test_dut_smoke.py` | partial write 测试 | 无数据值检查(弱断言) | 直接改写:加 `expected_data` 断言 + READ 数据校验 | Round 7 P0 |
| 14 | Generator `generator.py` | 基本随机读写 | 地址均匀分散,无法触发同 set replacement;缺 partial write/boundary 定向激励 | Prompt Tuning:见第三节 Case 1,重写 prompt 加入约束清单 | Round 2, Prompt Case 1 |
| 15 | RTL 微架构分析 | (UCAgent 无法生成) | UCAgent 不能分析 LRU round-robin vs 真 LRU、脏驱逐死锁状态机 | 人工审查 `NutShellCache.v`,定位 BUG-010/011 并写定向用例 | 能力边界 Case 1 |
| 16 | Verilator testbench `sim_main.cpp` | 初始 testbench | 对 `VlWide<16>` 512 位信号 int 赋值;缺 VCD/coverage API 调用顺序 | 直接改写:移除 int 赋值,补 include + API 顺序 | 能力边界 Case 2 |
| 17 | 跨环境集成 `.gitignore`/Docker | 初始规则 | 不知 xspcomm 符号链接致 Docker COPY 失败 | 直接改写:分层规则 `*.so` + `!DUT.so` | 能力边界 Case 3 |

## 三、Prompt Tuning 典型案例(指令微调记录)

### Case 1: Generator 约束优化(地址集中化)

- **Initial Prompt**: "生成一个 Cache 验证的随机激励生成器,包含 read 和 write 操作"
- **AI 缺陷**: 地址均匀分散,无法触发同 set replacement;无 partial write/boundary 定向激励;无法覆盖 `mask.sparse`、`replacement.dirty` 等 bins
- **Prompt 调整为**:
  ```
  生成 Cache 验证激励生成器,需要包含:
  1. CRV,地址集中在有限 set 范围以触发 replacement
  2. 定向激励:partial_write、replacement_sequence、line_boundary、RAW dependency
  3. 参数化:sets、ways、line_bytes 可配置
  4. 掩码约束:full / single / sparse 三种模式
  ```
- **改进结果**: `CacheGenerator` 实现 `random_stream`/`partial_write_sequence`/`replacement_sequence`/`line_boundary_sequence`,覆盖率从 ~60% 提升至 100%。

### Case 2: Scoreboard 循环论证修复(独立 oracle)

- **Initial Prompt**: "实现验证 Scoreboard,比对参考模型输出与 DUT 输出"
- **AI 缺陷**: `_run_stream` 把 `response = ref.access(txn)` 再与 `ref.access(txn)` 比较 —— 自比自,无法检测任何故障,覆盖率 100% 但验证无意义
- **Prompt 调整为**:
  ```
  重写验证 Scoreboard 使用独立验证方法论:
  1. 跟踪所有 WRITE 操作的数据和掩码
  2. READ 时用独立 oracle 验证已写字节
  3. CRV 验证确定性(同 seed 同结果)和覆盖率
  4. directed cases 验证具体数据值
  ```
- **改进结果**: 重写后成功检测 4 类故障注入;BUG-009 进一步修复 CRV eviction 假阳性。

### Case 3: Mock DUT 行为增强(贴近真实 Cache)

- **Initial Prompt**: "创建一个 Mock DUT 用于测试验证框架"
- **AI 缺陷**: `set_entry` 字典无限增长(永不驱逐),无 way 限制、无 LRU、无 writeback,与真实 NutShell Cache(4-way LRU)行为不一致
- **Prompt 调整为**:
  ```
  重写 Mock DUT 的 _process_request:
  1. way 限制(ways=4),满时 LRU 驱逐
  2. 驱逐 dirty 行时 writeback 到 backing memory
  3. miss 时从 memory fill
  4. 追踪 access_time 用于 LRU
  5. 行为与真实 NutShell Cache 一致
  ```
- **改进结果**: Mock DUT 实现完整 Cache 行为,后续真实 DUT 接入后行为一致。

## 四、Prompt 策略演进总结

| 阶段 | Prompt 策略 | 效果 |
| --- | --- | --- |
| Round 1-2 | 单一大指令("生成完整环境") | 框架可用但缺陷多,需大量 review |
| Round 3-4 | 聚焦指令(单一模块 + 明确约束) | 缺陷减少,定向 case 命中率提升 |
| Round 7 | 评审视角指令("以评审角度找问题") | 一次性发现 5 P0 + 4 P1 |
| Round 8-9 | 场景指令("接入真实 DUT"/"工业级 sign-off") | 触达 UCAgent 能力边界,转人工 |
| 经验 | **小而聚焦 > 大而全**;**约束清单 > 模糊描述**;**独立 oracle > 自比自** | — |

## 五、UCAgent 能力边界(人工不可替代)

| 能力维度 | UCAgent | 人工必需 |
| --- | --- | --- |
| 框架代码生成 | 强 | 审查和修改 |
| 约束随机激励 | 强 | 覆盖率目标设定 |
| RTL 微架构分析 | 弱 | 完全依赖人工 |
| 编译器特定错误(Verilator C++) | 弱 | 完全依赖人工 |
| 跨环境集成(WSL2/Docker/.gitignore) | 弱 | 完全依赖人工 |
| 测试用例设计 | 中 | 边界条件补充 |
| 文档生成 | 强 | 事实校验 |
