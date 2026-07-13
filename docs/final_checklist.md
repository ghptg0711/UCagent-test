# Final Checklist

本清单只记录当前可由代码或最新 CI 复核的状态；历史结果不自动继承。

## P0：参评资格

- [x] Apache-2.0 LICENSE
- [x] 标准工程目录
- [x] `.coverage`、native `.so`、原始 coverage 中间文件由 `.gitignore` 排除
- [x] native `.so` 已从 Git 索引移除，必须针对执行主机重新构建或 stage
- [x] Real DUT Adapter 不覆盖 DUT actual data
- [x] Reference expected 与 DUT actual 经独立 Scoreboard 比较
- [ ] Real DUT self-hosted CI PASS

## 可移植 Gate

- [x] 单元测试通过（数量以最新 CI 为准）
- [x] Core smoke/directed/CRV 通过独立 architectural byte oracle 数据检查
- [x] Core required bins 19/19；明确标记为 Reference Model coverage
- [x] 五类 fault 通过 ScoreboardMismatch 路径检出
- [x] DUT contract 测试证明 corrupted actual 会失败
- [x] Docker 使用 Python 3.14，运行 core 与 contract gate

## Real DUT Gate

- [ ] 固定 NutShell commit 可无绝对路径生成 RealNutShellCache RTL
- [ ] Picker 可在 CI/self-hosted runner 重建通用 ISA artifact
- [ ] Real DUT smoke（含 BUG-012 write-miss readback）PASS
- [ ] BUG-010 victim trace 动态复现并保存
- [ ] BUG-011 writeback → fill trace 动态复现并保存
- [ ] ≥3 Real DUT CRV seeds 各自 ≥90%，启用数据级 Scoreboard
- [ ] Real DUT Verilator line/branch/toggle/FSM coverage
- [ ] Real DUT VCD/FST artifact 与关键信号说明

## 报告一致性

- [x] 取消“Real DUT 100% coverage”和“100/100 已达一等奖”的无证据结论
- [x] Core、简化 RTL、Real DUT 三类证据分层
- [x] 历史大规模回归标记为非 sign-off
- [ ] coverage convergence 每轮绑定 commit SHA、命令、seed 和原始日志
- [ ] Real DUT Gate 完成后重新生成全部最终报告
