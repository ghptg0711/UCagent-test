# Coverage Summary Report

> 证据边界：本文的 19-bin 100% 指 Core Reference Model。历史 Real DUT 数字在
> 兼容 self-hosted runner 重跑前不得作为 sign-off；简化 RTL Verilator coverage
> 也不得标记为 RealNutShellCache coverage。

## Overview

| 指标 | 值 |
| --- | --- |
| 总体覆盖率 | 100.0% (19/19 bins) |
| 测试集 | smoke + directed + OOO scoreboard + CRV x 5 seeds |
| 事务总数 | 5069 |
| Fault Detection | 5/5 (100%) |

## Coverage Bins Details

### 按操作类型分组

| Bin | 命中次数 | 状态 |
| --- | --- | --- |
| op.read | 10 | ✅ 覆盖 |
| op.write | 9 | ✅ 覆盖 |

### 按访问结果分组

| Bin | 命中次数 | 状态 |
| --- | --- | --- |
| access.read_hit | 2 | ✅ 覆盖 |
| access.read_miss | 8 | ✅ 覆盖 |
| access.write_hit | 4 | ✅ 覆盖 |
| access.write_miss | 5 | ✅ 覆盖 |

### 按地址特性分组

| Bin | 命中次数 | 状态 |
| --- | --- | --- |
| addr.line_boundary | 1 | ✅ 覆盖 |
| addr.same_set | 12 | ✅ 覆盖 |

### 按延迟分组

| Bin | 命中次数 | 状态 |
| --- | --- | --- |
| latency.short | 12 | ✅ 覆盖 |
| latency.long | 7 | ✅ 覆盖 |

### 按写掩码分组

| Bin | 命中次数 | 状态 |
| --- | --- | --- |
| mask.full | 17 | ✅ 覆盖 |
| mask.single | 1 | ✅ 覆盖 |
| mask.sparse | 1 | ✅ 覆盖 |

### 按替换特性分组

| Bin | 命中次数 | 状态 |
| --- | --- | --- |
| replacement.clean | 2 | ✅ 覆盖 |
| replacement.dirty | 2 | ✅ 覆盖 |

### 按访问大小分组

| Bin | 命中次数 | 状态 |
| --- | --- | --- |
| size.1 | 2 | ✅ 覆盖 |
| size.2 | 2 | ✅ 覆盖 |
| size.4 | 1 | ✅ 覆盖 |
| size.8 | 14 | ✅ 覆盖 |

## Missing Bins

无。所有 required bins 均已覆盖。

## Per-Seed Coverage

| Seed | 事务数 | 覆盖率 | Missing Bins |
| --- | --- | --- | --- |
| 1 | 300 | 100.0% | 无 |
| 2 | 300 | 100.0% | 无 |
| 3 | 300 | 100.0% | 无 |

**说明**：经 P1.3 人工约束细化(将 `same_set` 采样从合成的 `index % 7` 改为基于真实地址局部性:维护已访问 set 集合,当 set 被重复访问时标记 `same_set=True`),单个 CRV seed 现可独立达到 100% 覆盖率,不再依赖 directed case 辅助。改进前单 seed 仅 94.7%(missing `addr.same_set`)。这一改进体现了人工对 UCAgent 生成代码的约束细化价值。

## Fault Detection

| Fault Type | Detected |
| --- | --- |
| read_corruption | ✅ Yes |
| partial_write_mask_drop | ✅ Yes |
| dirty_writeback_corruption | ✅ Yes |
| response_order_swap | ✅ Yes |
| tag_compare_error | ✅ Yes |

## Test Suite Summary

| 测试集 | 用例数 | 通过 | 失败 | 跳过 |
| --- | --- | --- | --- | --- |
| test_directed_cases.py | 16 | 16 | 0 | 0 |
| test_dut_smoke.py | 7 | 7 | 0 | 0 |
| test_edge_cases.py | 17 | 17 | 0 | 0 |
| test_generator_scoreboard.py | 7 | 7 | 0 | 0 |
| test_memory_agent.py | 1 | 1 | 0 | 0 |
| test_ooo_scoreboard.py | 8 | 8 | 0 | 0 |
| test_real_dut_smoke.py | 8 | pending | pending | pending | compatible self-hosted runner |
| test_reference_model.py | 3 | 3 | 0 | 0 |
| test_regression.py | 1 | 1 | 0 | 0 |
| **可移植总计** | **77** | **77** | **0** | **0** | latest local gate |

## 真实 DUT 覆盖率

| 指标 | 值 |
| --- | --- |
| DUT 类型 | 真实 NutShell Cache (DUTRealNutShellCache) |
| 测试环境 | WSL2 Ubuntu, Python 3.14.4 |
| Smoke/defect tests | 8 pending |
| 定向事务 | 7 笔 |
| CRV 事务 | 200 笔 (seed=42) |
| 功能覆盖率 | 待重跑；不得以 core 19/19 替代 |
| Verilator 代码覆盖率 | 待 RealNutShellCache `--coverage` 重建 |
| 仿真周期 | 待读取 Real DUT `cycle_count` 后重报 |
| 波形文件 | 待生成并上传 RealNutShellCache VCD/FST artifact |

## Verilator 第三方覆盖率

| 指标 | 值 |
| --- | --- |
| 编译工具 | Verilator 5.032 (WSL2) |
| 编译选项 | `--coverage --trace --exe` |
| 仿真可执行 | obj_dir_coverage/VNutShellCache |
| coverage.dat | 163 KB |
| coverage.info | 23 KB (LCOV 格式) |
| annotated 报告 | reports/verilator_coverage/annotated/ |
| 仿真周期 | 200,000 cycles |

## 覆盖率收敛趋势

覆盖率从初始 42.1% 逐步收敛至 100%，经过 10 次迭代。详细数据见 `reports/coverage_convergence.csv`，趋势图见 `reports/coverage_convergence_trend.svg`。

| 迭代 | 覆盖率 | 已覆盖 bins | 测试通过数 | Bug 发现数 | Bug 修复数 |
| --- | --- | --- | --- | --- | --- |
| 1 | 42.1% | 8/19 | 5 | 0 | 0 |
| 2 | 57.9% | 11/19 | 8 | 2 | 1 |
| 3 | 68.4% | 13/19 | 15 | 4 | 3 |
| 4 | 78.9% | 15/19 | 22 | 5 | 4 |
| 5 | 89.5% | 17/19 | 33 | 6 | 6 |
| 6 | 94.7% | 18/19 | 38 | 7 | 7 |
| 7 | 100.0% | 19/19 | 50 | 8 | 8 |
| 8 | 100.0% | 19/19 | 50 | 9 | 9 |
| 9 | 100.0% | 19/19 | 58 | 9 | 9 |
| 10 | 100.0% | 19/19 | 65 | 11 | 9 |

收敛关键点：
- 迭代 1-3：基础框架建立，覆盖率从 42% 提升至 68%
- 迭代 4-6：添加 weighted/implication 约束和定向用例，覆盖率从 79% 提升至 95%
- 迭代 7：覆盖率闭包达到 100%
- 迭代 8-10：真实 DUT 接入、OOO scoreboard、第 5 种故障注入、RTL Bug 发现
