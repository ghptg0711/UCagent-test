# 90 分目标优化路线

## 1. 评分目标拆解

如果目标是 90 分，建议不要只停留在 Python core。需要让评委看到三件事：

- 工程完整：结构清晰、命令可复现、文档齐全。
- 验证有效：能覆盖 Cache 关键风险，能通过 fault injection 证明可检错。
- 接近真实：至少完成 Toffee/Picker smoke 或给出明确、可执行的 DUT 接入边界。

## 2. 当前得分基础

当前已经具备较强基础：

| 项目 | 当前状态 | 对 90 分的价值 |
| --- | --- | --- |
| 仓库结构 | 完整 | 基础分 |
| 方案文档 | 已有多份 Markdown | 基础分和表达分 |
| 参考模型 | 支持 set/way/tag/LRU/dirty/writeback | 核心技术分 |
| 激励生成 | directed + CRV | 核心技术分 |
| scoreboard | 可比对 read/writeback/order | 核心技术分 |
| coverage | required bins 100% core closure | 核心技术分 |
| fault injection | 4 类 fault 检出 | 加分项 |
| WSL2 验证 | compileall/pytest/regression 通过，12 tests passed | 可复现分 |
| Memory agent | 已有协议无关 latency/backpressure model | DUT 接入加分基础 |

最大短板：

- 还没有真实 NutShell Cache DUT 的 Toffee/Picker 闭环。
- 还没有真实 RTL coverage 和波形证据。
- memory-side agent 仍未落地。

## 3. 优先级最高的优化

### P0：接入真实 DUT smoke

目标：拿到真实 NutShell Cache 的最小闭环。

任务：

1. 用 Picker 生成 Cache DUT Python 模型。
2. 填写 `configs/signal_map.yaml`。
3. 实现 `ToffeeCacheAdapter.reset()`。
4. 实现 CPU request drive 和 response sample。
5. 跑通 write then read smoke。

验收：

- scoreboard 无 mismatch。
- 保留命令、log、波形路径。
- 更新 `docs/verification_report.md`。

这是冲 90 分最关键的一步。

### P1：实现 memory agent

目标：让 miss/fill/writeback 由 testbench 可控，而不是只依赖 DUT 内部环境。

当前状态：core 级 `ScriptedMemoryAgent` 已完成，支持 latency、backpressure 和 masked write；仍需在 Toffee 层把真实 memory-side 信号接入。

任务：

- 监控 memory request。
- 对 read miss 返回 line fill。
- 捕获 dirty writeback。
- 支持可配置 latency。
- 支持 ready/valid backpressure。

验收：

- dirty eviction directed case 在真实 DUT 上通过。
- long latency 和 backpressure coverage bin 被打到。

### P2：扩大 directed cases

建议增加：

- 同 set `ways + 2` tag 循环访问，检查 LRU。
- partial write 跨多个 offset。
- read-after-write、write-after-read、write-after-write。
- line boundary 附近所有 size。
- uncached/MMIO 地址区间。
- reset 后状态清空。

验收：

- 每个 directed case 有名称、seed、预期行为、通过结果。
- 失败时能输出最小复现事务序列。

### P3：CRV seed 提升

目标从当前 core `3 seeds x 200 txns` 提升到：

- core：`10 seeds x 1000 txns`。
- DUT：至少 `3 seeds x 300 txns`。

优化点：

- 为每个 seed 输出 coverage。
- 失败自动打印 transaction index。
- 记录最后 20 条事务作为复现窗口。

### P4：覆盖率报告可视化

当前状态：`reports/core_regression_summary.md` 已输出 required bin hit table。后续建议继续增加：

- Markdown 表格列出每个 bin 的 hit count。
- 按 op/size/mask/replacement/latency 分组。
- 把 missing bins 单独列出。

这会显著提升报告质量。

### P5：AI 协作痕迹增强

建议补充：

- prompt 摘要。
- AI 初稿问题。
- 人工 review 修改点。
- bug 修复前后对比。

重点是说明你不是直接复制 AI 输出，而是用 AI 提效，并有人为验证闭环。

## 4. 90 分版本建议交付物

| 类型 | 文件 |
| --- | --- |
| 赛题说明 | `docs/contest_statement.md` |
| 整体方案 | `docs/overall_solution.md` |
| 验收文档 | `docs/acceptance_document.md` |
| 验证报告 | `docs/verification_report.md` |
| 90 分优化路线 | `docs/score_90_optimization_plan.md` |
| 最终检查清单 | `docs/final_checklist.md` |
| 覆盖率摘要 | `reports/coverage_summary.md` |
| core regression 摘要 | `reports/core_regression_summary.md/json` |
| bug 记录 | `reports/bug_tracker.md` |
| AI 协作记录 | `reports/ai_collaboration_log.md` |

## 5. 建议时间安排

| 阶段 | 时间 | 目标 |
| --- | --- | --- |
| Day 1 | 2-4 小时 | 完成 Picker/Toffee smoke |
| Day 2 | 4-6 小时 | memory agent + dirty eviction DUT case |
| Day 3 | 2-4 小时 | directed cases 扩展和 coverage 表格 |
| Day 4 | 2-3 小时 | 多 seed regression 和报告更新 |
| Day 5 | 1-2 小时 | 最终检查、压缩包清理、答辩材料 |

## 6. 90 分判断标准

达到以下状态时，比较接近 90 分：

- [ ] 真实 DUT smoke 跑通。
- [ ] 至少 3 个真实 DUT directed case 跑通。
- [ ] dirty eviction 在真实 DUT 上有观测证据。
- [ ] core coverage 100%，DUT functional coverage 不低于 90% 或有合理解释。
- [ ] fault injection 4/4 core 检出，至少 1 个 DUT 边界 fault 可检出。
- [ ] 文档完整，命令可复现。
- [ ] bug tracker 和 AI collaboration log 有真实内容。

如果无法接入真实 DUT，要拿 90 分会明显更难。此时应把 core 做到更完整：增加 policy 参数化、coverage 表格、更多 fault injection、更多 directed cases，并在报告中诚实说明 DUT 接入阻塞点。
