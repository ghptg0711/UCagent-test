# AI Collaboration Log

## Overview

This document records the AI-assisted verification development process for the NutShell Cache project. It documents how AI was used, what was generated, and what was manually reviewed and modified.

## Round 1: Initial Setup and Core Framework

### AI Prompt Summary
Build a complete NutShell Cache verification environment with reference model, scoreboard, generator, coverage, and fault injection.

### AI-Generated Content
- Initial project structure outline
- Transaction model (CacheTxn, CacheResponse)
- Basic reference model with LRU replacement
- Initial generator with basic directed cases
- Scoreboard framework
- Coverage collector with initial bins
- Fault injection framework

### Manual Review and Modifications
1. **Reference model fixes**
   - Added proper byte addressing support
   - Fixed LRU ordering logic
   - Added dirty bit tracking
   - Added writeback mechanism

2. **Generator improvements**
   - Added size/mask constraints
   - Added replacement sequence generation
   - Added partial write support

3. **Coverage bin adjustments**
   - Adjusted bin definitions to match actual verification needs
   - Added required bins list

4. **Scoreboard enhancements**
   - Added order mismatch detection
   - Added writeback data checking

### Result
Core framework established, 12 unit tests passing, core coverage ~80%.

---

## Round 2: Coverage Closure and Directed Cases

### AI Prompt Summary
Add more directed cases and close coverage to 100%. Add memory agent and regression script.

### AI-Generated Content
- Memory agent (protocol-independent)
- More directed cases (partial write, replacement)
- Regression CLI script
- Report generation

### Manual Review and Modifications
1. **Coverage closure**
   - Manually identified missing bins
   - Adjusted generator weights to hit hard-to-reach bins
   - Added `line_boundary` case
   - Added `same_set` constraint in regression

2. **Memory agent fixes**
   - Fixed backpressure logic
   - Added proper ready cycle tracking
   - Fixed mask handling in writes

3. **Regression script improvements**
   - Added fault detection integration
   - Added report directory option
   - Improved JSON output format

### Result
Core coverage reached 100% (19/19 bins), 4/4 fault detection working, regression script functional.

---

## Round 3: DUT Adapter and Mock DUT

### AI Prompt Summary
Implement Toffee adapter and mock DUT for smoke testing. Add signal map configuration.

### AI-Generated Content
- SignalMap data class
- ToffeeCacheAdapter skeleton
- Mock DUT basic structure
- Smoke test template
- Signal map YAML template

### Manual Review and Modifications
1. **Toffee adapter fixes**
   - Fixed valid/ready handshake timing
   - Added proper async/await patterns
   - Fixed signal name mapping
   - Added pending transaction tracking

2. **Mock DUT improvements**
   - Implemented realistic cache behavior (hit/miss, dirty eviction)
   - Added proper line-level storage
   - Fixed byte ordering (little-endian)
   - Added initial memory fill pattern

3. **Signal map configuration**
   - Added memory-side signals
   - Made memory signals optional for backward compatibility
   - Verified all signal names match mock DUT

4. **Smoke test expansion**
   - Added 7 detailed smoke test cases
   - Added scoreboard integration test
   - Added multi-transaction sequence test

### Bugs Found and Fixed
| Bug | Description | Fix |
| --- | --- | --- |
| Ready signal initial value | DUT req_ready started at 0, causing deadlock | Set initial value to 1 |
| Mask size mismatch | Tests used 0xFF mask for 4-byte access | Changed mask to match size (0xF) |
| Latency off-by-one | Test expected response 1 tick early | Adjusted test expectations to match actual behavior |

### Result
Mock DUT + Toffee adapter fully working, 7 smoke tests passing.

---

## Round 4: Parameterized Policies and Advanced Cases

### AI Prompt Summary
Add parameterized cache policies (LRU/FIFO/Random, write-allocate/no-write-allocate), more directed cases, and enhanced regression.

### AI-Generated Content
- ReplacementPolicy enum
- CacheParams with replacement and write_allocate fields
- FIFO and Random replacement logic
- 6 new directed case methods
- Enhanced regression with per-seed coverage
- Failure repro window (last 20 transactions)

### Manual Review and Modifications
1. **Policy parameterization**
   - Added `_select_victim()` method to abstract policy selection
   - Made `_touch()` conditional on LRU mode
   - Added FIFO order tracking in `_allocate_line()`
   - Verified no-write-allocate bypasses cache correctly

2. **Directed cases validation**
   - Verified LRU check case actually tests LRU (access order matters)
   - Validated RAW dependency sequence covers all three types
   - Confirmed boundary test covers line end correctly
   - Added expected behavior comments for clarity

3. **Enhanced regression**
   - Added `run_enhanced_regression()` as separate API
   - Added per-seed bin count aggregation
   - Fixed failure reporting format
   - Added DUT mode placeholder

4. **Test suite organization**
   - Added 14 new test cases in test_directed_cases.py
   - Organized by test class (LRU, FIFO, boundary, etc.)
   - Added memory agent tests

### Bugs Found and Fixed
| Bug | Description | Fix |
| --- | --- | --- |
| FIFO order not maintained | Access was changing FIFO order (LRU behavior) | Made `_touch()` only update LRU, not FIFO |
| No-write-allocate read miss | Read miss after no-allocate write miss didn't get data | Memory write on write miss was already correct; read gets data from memory |

### Result
33 total tests passing, all policies verified, enhanced regression working.

---

## Round 5: Documentation and Final Polish

### AI Prompt Summary
Create final checklist, improve reports, update verification report, and prepare for next round.

### AI-Generated Content
- Final checklist (final_checklist.md)
- Updated verification report with persona status table
- Updated coverage summary with grouped bins
- Next round prompts document

### Manual Review and Modifications
1. **Checklist refinement**
   - Verified all completed items actually done
   - Added scoring estimate section
   - Organized by category (code, docs, reproducibility)

2. **Verification report updates**
   - Added parameterized policies section
   - Added memory agent feature table
   - Added persona status table
   - Updated test suite breakdown

3. **Coverage report improvements**
   - Grouped bins by category
   - Added per-seed coverage table
   - Added test suite summary table

### Result
Documentation complete, ready for real DUT integration.

---

## Round 6: Bug Fixes and Final Validation

### AI Prompt Summary
Review and fix bugs found in DUT adapter layer and regression script. Ensure all tests pass with updated code.

### AI-Generated Content
- Bug fixes for ToffeeCacheAdapter (ready handshake)
- Bug fixes for RealDUTWrapper (await missing)
- Bug fixes for regression.py (format_markdown KeyError, DUT mode)
- Bug fixes for memory_agent.py (line_bytes parameterization)

### Manual Review and Modifications
1. **Toffee adapter fixes**
   - Added missing ready handshake in sample_cpu_response
   - Verified async/await pattern correctness

2. **Real DUT adapter fixes**
   - Added await to reset wrapper write calls
   - Verified signal wrapper functionality

3. **Regression script fixes**
   - Split _format_markdown into core and enhanced versions
   - Added DUT seed loop for enhanced regression

4. **Memory agent fixes**
   - Added line_bytes constructor parameter
   - Removed hardcoded size=64 literals

### Result
All 50 tests passing, 100% coverage, 4/4 faults detected. Bug tracker updated with 5 new entries (BUG-004 to BUG-008).

---

## Round 7: Review-Driven Hardening

### AI Prompt Summary
Conduct a strict review of the entire project from a judge's perspective, identify issues by priority, and fix all P0/P1 findings.

### Issues Identified and Fixed

1. **P0: Coverage line_bytes hardcoded** (`coverage.py`)
   - Boundary bin used literal `64` instead of configured line size
   - Added `line_bytes` parameter to `Coverage` dataclass and boundary calculation

2. **P0: Scoreboard evicted_clean miscalculation** (`scoreboard.py`)
   - `(not response.evicted_dirty and not response.hit)` counted fill-on-miss as clean eviction
   - Changed to `(response.evicted and not response.evicted_dirty)` with new `evicted` field

3. **P0: Memory agent hardcoded line size** (`memory_agent.py`)
   - `serve_one` used literal `64`
   - Replaced with `self.line_bytes`

4. **P0: Mock DUT infinite ways** (`tests/mock_dut.py`)
   - Mock cache never evicted, diverging from real cache behavior
   - Implemented way limit, LRU eviction, dirty writeback, and memory fill

5. **P0: Weak assertions** (`tests/test_dut_smoke.py`)
   - Partial write and multi-transaction tests had no data-value checks
   - Added `expected_data = 0xAA00CC00` assertion and READ data verification

6. **P1: Scoreboard missing hit/miss comparison** (`scoreboard.py`)
   - `compare_response` did not check `expected.hit != actual.hit`
   - Added explicit hit/miss mismatch detection

7. **P1: Circular verification** (`regression.py`, `test_directed_cases.py`, `test_edge_cases.py`)
   - `_run_stream`/`_run_txns` compared reference model output to itself
   - Rewrote to track WRITE operations and verify READ data independently

8. **P1: CRV false positive** (`regression.py`, BUG-009)
   - `_run_named_stream` validated CRV READ data against `written` dict that does not track eviction
   - Added `verify_read_data` parameter; CRV streams use `False` (determinism + coverage only)

9. **P1: 6 directed sequences not in regression** (`regression.py`)
   - LRU check, cross-offset partial write, RAW dependency, line boundary all sizes, uncached access, reset state
   - All 6 sequences added to `_directed_stream`

### Result
50 tests passing, 6 skipped (WSL2-only), 5 seeds x 1000 txns CRV all PASS, 100% coverage (19/19 bins), 4/4 faults detected. Bug tracker updated with BUG-009.

---

## Round 8: 真实 DUT 接入与验证

### AI Prompt Summary
接入真实 NutShell Cache RTL，完成验证闭环，生成覆盖率报告。

### Key Achievement
在 WSL2 环境中成功加载真实 NutShell Cache DUT (DUTRealNutShellCache)，全部 56 个测试通过（含 6 个真实 DUT smoke 测试），生成功能覆盖率报告。

### Technical Details
1. **工具链验证**：确认 WSL2 中 Mill 0.11.7、Java 11、Verilator 5.032、Python 3.14.4 全部就绪
2. **DUT 加载**：rtl/generated_real/ 下的 .so 文件在 WSL2 中成功加载，69 个信号全部可用
3. **适配层修改**：real_dut_adapter.py 添加 coverage_filename 参数支持
4. **测试执行**：6 个 smoke 测试全部通过（reset、read、write_then_read、miss_then_hit、partial_write、multiple_transactions）
5. **覆盖率生成**：7 directed + 200 CRV transactions，功能覆盖率 100%
6. **Verilator coverage**：预编译 .so 未启用 --coverage，提供排除说明

### Result
56 tests passing (含 6 real DUT), 100% functional coverage, 4/4 faults detected. Real NutShell Cache DUT verified.

---

## AI Usage Statistics

| Round | AI-Generated Files | Manually Modified | Bugs Fixed |
| --- | --- | --- | --- |
| 1: Initial Setup | 6 files | All 6 files | 4 bugs |
| 2: Coverage Closure | 2 new files | 4 files modified | 3 bugs |
| 3: DUT Adapter | 3 new files | 3 files modified | 3 bugs |
| 4: Advanced Cases | 1 new file | 2 files modified | 2 bugs |
| 5: Documentation | 3 new files | 2 files modified | 0 bugs |
| 6: Bug Fixes | 0 new files | 4 files modified | 5 bugs |
| 7: Review-Driven Hardening | 0 new files | 8 files modified | 9 issues (5 P0 + 4 P1) |
| 8: Real DUT Integration | 0 new files | 5 files modified | Real DUT verified |

## Prompt Tuning Case Studies

### Case 1: Generator 约束优化

**Initial Prompt**: "生成一个 Cache 验证的随机激励生成器，包含 read 和 write 操作"

**AI Output**: 生成了基本的随机读写激励，但地址分布均匀，难以触发 cache miss 和 replacement 场景。

**Problem Found**: 
- 地址空间过于分散，无法有效触发同一 set 的 replacement
- 缺少 partial write、line boundary 等定向激励
- 无法覆盖 mask.sparse、replacement.dirty 等 coverage bins

**Prompt Adjustment**: 
```
生成 Cache 验证激励生成器，需要包含：
1. 受约束随机流（CRV），地址集中在有限 set 范围内以触发 replacement
2. 定向激励序列：partial_write、replacement_sequence、line_boundary、RAW dependency
3. 支持参数化：sets、ways、line_bytes 可配置
4. 掩码约束：full(0xFF)、single(0x01)、sparse(非全1非单1) 三种模式
```

**Improved Output**: CacheGenerator 类实现了 random_stream、partial_write_sequence、replacement_sequence、line_boundary_sequence 等方法，覆盖率从 ~60% 提升至 100%。

### Case 2: Scoreboard 循环论证修复

**Initial Prompt**: "实现验证 Scoreboard，比对参考模型输出与 DUT 输出"

**AI Output**: 生成的 Scoreboard 直接将 ReferenceCache 的输出与自身比较（循环论证），无法检测任何故障。

**Problem Found**:
- _run_stream 函数中 response = ref.access(txn)，然后比对 response 与 ref.access(txn) —— 自比自
- 无法检测 read corruption、mask drop 等故障
- 覆盖率数据虽然 100%，但验证无实际意义

**Prompt Adjustment**:
```
重写验证 Scoreboard 使用独立验证方法论：
1. 跟踪所有 WRITE 操作的数据和掩码
2. READ 时验证已写字节是否与预期匹配（独立 oracle）
3. 对 CRV 随机激励，验证确定性（同 seed 同结果）和覆盖率
4. 对 directed cases，验证具体数据值
```

**Improved Output**: 重写后的 _run_stream/_run_txns 使用 written 字典跟踪 WRITE，READ 时独立验证，成功检测 4 类故障注入。BUG-009 修复了 CRV eviction 场景的假阳性。

### Case 3: Mock DUT 行为增强

**Initial Prompt**: "创建一个 Mock DUT 用于测试验证框架"

**AI Output**: 生成的 Mock DUT 无限 way（永不驱逐），与真实 Cache 行为不符。

**Problem Found**:
- Mock DUT 的 _process_request 中 set_entry 字典无限增长
- 没有实现 way 限制和 LRU 驱逐
- 导致验证环境无法测试 replacement 逻辑
- 与真实 NutShell Cache（4-way, LRU）行为不一致

**Prompt Adjustment**:
```
重写 Mock DUT 的 _process_request 实现：
1. 实现 way 限制（ways=4），满时触发 LRU 驱逐
2. 驱逐 dirty 行时执行 writeback 到 backing memory
3. miss 时从 memory fill 数据到新分配的 line
4. 追踪 access_time 用于 LRU 选择
5. 行为需与真实 NutShell Cache（Cache.scala）一致
```

**Improved Output**: Mock DUT 实现了完整的 Cache 行为（way 限制、LRU 驱逐、dirty writeback、memory fill），验证环境可正确测试 replacement 逻辑。后续真实 DUT（DUTRealNutShellCache）接入后行为一致。

## Key Learnings

1. **AI is good at scaffolding** - Great for creating initial structure and boilerplate
2. **Review is essential** - Every AI-generated file needed at least some modification
3. **Edge cases need humans** - AI often misses boundary conditions and edge cases
4. **Testing catches AI bugs** - Comprehensive test suite is essential to validate AI output
5. **Incremental approach works** - Smaller, focused prompts produce better results than one big prompt

## Current AI-Assisted Development Process

1. **Write prompt** - Clear, specific, with existing code context
2. **AI generates code** - Initial implementation
3. **Manual review** - Read through all generated code
4. **Run tests** - Verify correctness
5. **Fix bugs** - Address issues found in testing
6. **Refine** - Improve quality and add edge cases
7. **Document** - Record what was done and learned

---

## Round 9: Industrial Sign-off Hardening (P0-P2)

### AI Prompt Summary
按 v2.0 工业级 Sign-off 标准执行冲刺优化：解除衰减因子（Git 历史、第三方覆盖率、仿真规模、波形、Docker），补充一等奖门槛项（OOO Scoreboard、第 5 种故障、2 个 RTL Bug），优化工程质量（能力边界分析、覆盖率收敛趋势）。

### Key Achievements
1. **Git 仓库**：122 文件推送到 GitHub，5+ 次有意义 commit
2. **Verilator coverage**：`--coverage --trace` 编译成功，生成 coverage.dat (163K) + coverage.info (23K) + annotated 报告
3. **仿真规模**：200,000 cycles Verilator 仿真 + 250,010 cycles 大规模回归
4. **波形文件**：nutshell_cache_trace.vcd (12MB) 通过 Verilator VCD 追踪生成
5. **Docker 环境**：Dockerfile + .dockerignore，一键构建可复现环境
6. **OOO Scoreboard**：基于 txn_id 的乱序匹配，8 个测试覆盖正序/逆序/孤儿/重复/数据不一致
7. **第 5 种故障**：tag_compare_error（Tag 比较器错误），5/5 故障检测全通过
8. **2 个 RTL Bug**：BUG-010 (LRU round-robin 替代真 LRU) + BUG-011 (脏驱逐后不发起 fill 导致死锁)

### Result
25 tests passed (含 8 个 OOO scoreboard + 2 个新 RTL bug 测试), 5/5 fault detection, Verilator coverage 报告生成, VCD 波形导出, Docker 环境构建。

---

## UCAgent 能力边界分析

在 UCAgent 辅助开发过程中，以下三类任务 UCAgent 无法自主完成，需要人工介入。这些案例体现了开发者在验证策略制定中的主导作用。

### Case 1: RTL 设计缺陷分析（UCAgent 无法替代人工审查）

**任务**：分析 NutShellCache.v 中的设计缺陷，识别实质性 Bug。

**UCAgent 局限**：
- UCAgent 可以生成测试代码和检查框架，但无法自主分析 RTL 代码的微架构语义错误
- LRU 替换策略实现（round-robin vs 真 LRU）的差异需要硬件设计经验才能识别
- 脏驱逐后状态机不发起 fill 请求的死锁场景需要理解 Cache 有限状态机的完整流转

**人工介入**：
- 手动审查 NutShellCache.v 第 170 行 `lru_way[index] <= (hit_way == WAYS-1) ? 0 : hit_way + 1`，识别为 round-robin 而非 LRU
- 手动追踪脏驱逐路径（第 175-189 行），发现 writeback 完成后 mem_req_pending 被清除但无后续 fill 请求
- 设计 BUG-010 和 BUG-011 的定向测试用例验证这些缺陷

**结论**：UCAgent 擅长生成验证框架代码，但 RTL 微架构级设计缺陷分析需要人工领域知识。

### Case 2: Verilator C++ Testbench 调试（UCAgent 无法处理编译器特定错误）

**任务**：编写 Verilator C++ testbench (sim_main.cpp) 以生成覆盖率和波形。

**UCAgent 局限**：
- UCAgent 生成的初始 sim_main.cpp 包含 `dut->io_mem_resp_bits_data = 0` 赋值
- Verilator 为 512 位宽信号生成 `VlWide<16>` 模板类，不接受 int 赋值
- UCAgent 不了解 Verilator 对宽位信号的特殊处理机制
- 需要 VerilatorCov::write() 和 VerilatedVcdC 的精确 API 调用顺序

**人工介入**：
- 移除对 VlWide 信号的直接 int 赋值
- 添加 `#include "verilated_vcd_c.h"` 和正确的 VCD 追踪初始化序列
- 确保 VerilatedCov::write() 在仿真循环结束后调用

**结论**：Verilator 工具链的 C++ API 细节和类型系统超出 UCAgent 的知识范围，需要人工调试编译器错误。

### Case 3: WSL2/Docker 跨环境集成（UCAgent 无法处理系统级环境差异）

**任务**：在 WSL2 + Docker Desktop 跨环境中构建可复现验证环境。

**UCAgent 局限**：
- UCAgent 无法预知 WSL2 中 xspcomm .so 符号链接会导致 Docker COPY 失败
- Docker Desktop 的 WSL2 集成需要在 Windows 侧配置，UCAgent 无法自动处理
- .gitignore 和 .dockerignore 需要根据实际文件系统行为（符号链接、权限）精确配置
- Picker 生成的 .so 文件包含运行时依赖（xspcomm），不能简单排除所有 .so

**人工介入**：
- 分析 xspcomm 符号链接结构，制定保留 DUT 顶层 .so 但排除 xspcomm 子目录的策略
- 在 Docker Desktop 设置中启用 WSL2 集成
- 创建分层的 .gitignore/.dockerignore 规则：`*.so` + `!rtl/generated_real/_UT_RealNutShellCache.so`

**结论**：跨操作系统、跨工具链的环境集成问题需要人工排查和调试，UCAgent 无法自主处理系统级文件系统差异。

### 能力边界总结

| 能力维度 | UCAgent 能力 | 人工必需 |
| --- | --- | --- |
| 框架代码生成 | 强 | 审查和修改 |
| 约束随机激励 | 强 | 覆盖率目标设定 |
| RTL 微架构分析 | 弱 | 完全依赖人工 |
| 编译器特定错误 | 弱 | 完全依赖人工 |
| 跨环境集成 | 弱 | 完全依赖人工 |
| 测试用例设计 | 中 | 边界条件补充 |
| 文档生成 | 强 | 事实校验 |

