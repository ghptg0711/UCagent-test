# 赛题说明

本文档描述 NutShell Cache 模块验证赛题的目标、验证对象和验收标准。这些规范为参赛者提供明确的交付边界，同时为评审提供一致的检查清单。

## 核心目标

构建可复现、可扩展、能发现典型 Cache 设计缺陷的验证方案。核心目标不是跑通少量样例，而是建立一套完整的验证体系。

## 验证对象

验证对象为 NutShell Cache 或 NutShell-like Cache DUT。典型接口：

| 接口类型 | 信号描述 |
| --- | --- |
| CPU 侧请求/响应 | 地址、读写控制、写数据、写 mask、valid/ready、读返回数据 |
| Memory 侧 | miss fill、dirty writeback、响应延迟、backpressure |
| 时钟复位 | clock、reset |

真实 DUT 接入时，需要根据 Picker 生成结果和 RTL 端口确认具体信号名，并落到 `configs/signal_map.yaml`。

## 验证角色与关注点

在 Cache 验证任务中，验证工作按职责划分为五个角色，每个角色有其独立的关注点和检查清单：

| 角色 | 关注点 | 检查清单 |
| --- | --- | --- |
| 验证架构师 | 验证方案是否完整、可复现？ | [功能覆盖](#功能覆盖) |
| 测试工程师 | 测试用例是否充分、激励是否有效？ | [测试激励](#测试激励) |
| 协议专家 | Cache 行为是否符合协议规范？ | [协议符合性](#协议符合性) |
| 性能分析师 | 边界条件和性能压力是否覆盖？ | [边界与压力](#边界与压力) |
| 文档工程师 | 提交物是否完整、报告是否清晰？ | [提交物规范](#提交物规范) |

### 功能覆盖

验证架构师负责确保验证方案的功能完整性：

- Read miss 后从下级 memory fill。
- Read hit 返回 cache line 中的数据。
- Write hit 更新 line data，并正确处理 byte mask。
- Write miss 分配 line 或按 DUT 策略处理。

### 测试激励

测试工程师负责生成有效的测试激励：

- 同 set 多 tag 访问触发 replacement。
- Dirty line eviction 时写回旧 line。
- Clean line eviction 不产生错误写回。
- 不同访问大小：1B、2B、4B、8B。

### 协议符合性

协议专家负责验证 Cache 行为的协议正确性：

- line 边界附近访问。
- memory latency 和 backpressure。
- 响应顺序和事务匹配。

### 边界与压力

性能分析师负责覆盖边界条件和压力场景：

- 极端地址对齐情况。
- 高并发访问下的冲突处理。
- memory 响应延迟变化。

### 提交物规范

文档工程师负责确保提交物的完整性和规范性：

| 路径 | 内容 |
| --- | --- |
| `src/cache_vip/` | 可复用 Cache 验证核心 |
| `tests/` | DUT-independent 单元测试和负向测试 |
| `configs/` | DUT 信号映射样例 |
| `docs/contest_statement.md` | 赛题说明 |
| `docs/overall_solution.md` | 整体赛题方案 |
| `docs/acceptance_document.md` | 验收文档 |
| `docs/verification_report.md` | 当前验证报告 |
| `docs/score_90_optimization_plan.md` | 90 分目标优化路线 |
| `reports/` | 覆盖率、bug、AI 协作和回归摘要 |

## 当前完成边界

当前已完成 DUT-independent verification core：

- 参考模型、激励生成器、scoreboard、coverage、fault injection。
- WSL2 下 Python 单测和 core regression 通过。
- core required coverage bins 达到 100%。
- 4 类 fault injection 均可检出。

未完成真实 RTL 绑定：

- `src/cache_vip/toffee_adapter.py` 仍是稳定边界层。
- 真实 NutShell Cache Picker 产物和具体信号名需要在最终 WSL2 环境中补齐。
- RTL 实测覆盖率和真实 bug 波形需要接入 DUT 后更新。
