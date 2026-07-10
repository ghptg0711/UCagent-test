# NutShell Cache 验证报告

## 1. 项目概述

- DUT：
- RTL commit：
- UCAgent commit/version：
- Toffee version：
- Picker version：
- 仿真器：
- 验证负责人：

## 2. 测试计划

| 类别 | 用例 | 目标 | 状态 |
| --- | --- | --- | --- |
| Smoke | reset/read/write | 基础闭环 | TODO |
| Directed | dirty eviction | 写回正确性 | TODO |
| Directed | partial write | byte mask merge | TODO |
| CRV | weighted random | 高覆盖随机 | TODO |
| Stress | memory latency | 回压稳定性 | TODO |
| Fault | data corruption | 证明可检出 | TODO |

## 3. 覆盖率分析

| 覆盖项 | 目标 | 实际 | 说明 |
| --- | ---: | ---: | --- |
| op | 100% | TODO | read/write |
| size | 100% | TODO | 1/2/4/8B |
| hit/miss | 100% | TODO | read/write cross |
| replacement | 90% | TODO | clean/dirty/all ways |
| mask | 90% | TODO | full/single/sparse |
| latency | 90% | TODO | short/long/backpressure |
| 总体 | >=90% | TODO |  |

## 4. Bug 追踪记录

| ID | 类型 | 现象 | 复现 seed/序列 | 根因 | 状态 |
| --- | --- | --- | --- | --- | --- |
| BUG-001 | TODO | TODO | TODO | TODO | OPEN |

## 5. AI 协同与人工修正

| 模块 | AI 初始产物 | 人工发现的问题 | 人工修正 | 价值 |
| --- | --- | --- | --- | --- |
| Generator | 基础随机读写 | 缺少替换和 partial write corner | 增加定向约束序列 | 提高覆盖 |
| Scoreboard | 简单 memory dict | 未建模 dirty eviction | 增加 set/way/tag/dirty/LRU | 检出写回 bug |
| Coverage | 简单计数 | 无 cross coverage | 增加 op x hit/miss 等 cross | 量化完备性 |

## 6. 结论

- 回归结论：
- 覆盖率结论：
- 已知限制：
- 后续改进：

