# NutShell Cache 提交评审与整改状态

**更新时间**：2026-07-13

**状态**：整改中，尚未达到真实 DUT sign-off

## 证据分层

| 层级 | 当前状态 | 可支持的结论 |
| --- | --- | --- |
| Core Reference Model | PASS | 19/19 required bins；CRV 使用独立 byte-level architectural oracle |
| DUT contract | PASS | expected/actual 分离；Scoreboard 可检出独立 actual 错误；Adapter 不覆盖 DUT 数据 |
| 简化 RTL Verilator | 有历史结果 | 仅对应 `rtl/dut_gen/NutShellCache.v`，不能代表 RealNutShellCache |
| RealNutShellCache | 待重跑 | 历史 `.so` 使用 Python 3.14 ABI 和 `-march=native`，GitHub-hosted runner 不兼容 |

## 当前有效 Gate

```bash
python -m pytest tests --ignore=tests/test_real_dut_smoke.py
PYTHONPATH=src python -m cache_vip.regression --seeds 1,2,3 --count 300
docker build .
```

真实 DUT Gate 必须在带 `real-dut` 标签、CPU 兼容且安装 Picker/xspcomm 的
self-hosted Linux runner 上手工触发。未取得该 job 的 PASS 结果前，不得声明：

- Real DUT smoke 通过；
- Real DUT functional coverage 达到 90% 或 100%；
- BUG-010/011/012 已由真实 DUT 动态复现；
- VCD/Verilator coverage 属于 RealNutShellCache。

## 已完成整改

- `.coverage`、coverage XML/HTML 输出加入 `.gitignore`；移除所有不可移植 `.so` 二进制；
- Real DUT Adapter 不再用软件内存覆盖 DUT `rdata`；hit 从实际 memory_reads 事件推导；
- 无法观测的 hit/replacement 字段显式标记为未观测；
- 新增 `DUTRegressionRunner`，形成 reference expected → DUT actual → Scoreboard；
- CRV 恢复数据级检查，使用独立 byte oracle 跟踪 masked write 和 eviction 后读回；
- **P1.2 完成**：五类 fault detection 全部经 `good_ref + faulty_ref + ScoreboardMismatch` 端到端链路判定，不再只比较注入前后字段；
- **P1.3 完成**：新增 BUG-012（write-miss 数据丢失）Reference Model 定向测试和 bug_tracker 记录；
- coverage closure 的 `same_set` 改为真实地址 set revisit；
- **CI 增强**：unit-tests job 上传回归报告；dut-contract-tests 扩展为完整可移植套件 + coverage artifact；real-dut-tests 增加 CRV、缺陷测试、coverage 生成、artifact 上传；
- **build_real_dut.sh 增强**：加 Python/Verilator 版本校验，输出版本、CPU、编译参数 build manifest；
- Docker/hosted CI 与 native Real DUT Gate 明确分离。

## 当前评分预估（基于已完成整改，不含 Real DUT Gate）

| 维度 | 子项 | 满分 | 当前 | 说明 |
| --- | --- | --- | --- | --- |
| 实操深度 | 基础环境构建 | 20 | 16 | Picker 脚本齐全但需 self-hosted runner；Toffee/Adapter/Memory/Scoreboard 闭环完整 |
| 实操深度 | 人工干预与优化 | 25 | 22 | OOO scoreboard、参数化模型、端到端故障检测、3 个 RTL 缺陷分析；缺真实 DUT 故障链路证据 |
| 实操深度 | 覆盖率达标 | 15 | 8 | Reference Model 100% 且 3 seeds 独立达标；真实 DUT coverage 待跑 |
| 报告协同 | 协同过程记录 | 20 | 18 | 17 条缺陷对比表 + Prompt 策略演进 + 多轮记录 |
| 报告协同 | 工程规范与可复现性 | 20 | 13 | 源码构建脚本、manifest、artifact 上传；缺 CI 绿色和真实 DUT 证据 |
| **合计** | | **100** | **77** | 二等奖上限，距一等奖差 8 分 |

> 关键差距（8 分）：真实 DUT coverage（7 分）+ CI 绿色（1 分）。
> 一旦 self-hosted runner 跑通 Real DUT Gate，可升至约 88-92 分（一等奖区间）。

## 未完成阻塞项

1. 将固定提交的 NutShell RTL 与 Picker 导出链改造成无本机绝对路径的 CI 构建脚本；
2. 生成不含 `-march=native`、匹配 Python 3.14 的 RealNutShellCache artifact；
3. 在真实 DUT 上跑 ≥3 seeds，并由 DUT-observed monitor 采样 coverage；
4. 生成真实 RealNutShellCache VCD/FST 和 Verilator coverage；
5. 为 BUG-010/011/012 保存真实 failing trace、timeout 和最小复现日志。

## 当前评分声明

在上述阻塞项完成前，不保留历史“100/100、一等奖条件全部满足”的自评结论。
最终分数必须以最新 CI、真实 DUT 日志和可下载 artifact 为准。
