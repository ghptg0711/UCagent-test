# NutShell Cache 提交评审与整改状态

**更新时间**：2026-07-13

**状态**：整改中，尚未达到真实 DUT sign-off

## v2.0 严苛版终审审计结果

### 🔴 一票否决项检查

| 项 | 结果 | 说明 |
| --- | --- | --- |
| LICENSE | ✅ | Apache 2.0，OSI 认证许可 |
| 目录结构 | ✅ | 无 >1MB 二进制，.so/.vcd/.fst/.pyc 均在 .gitignore |
| 仓库卫生 | ✅ | 无密钥泄露，git fsck 完整，无 whitespace 错误 |
| AI 纯度 | ✅ | git blame 显示核心组件由 "UCagent Team" 和 "ghptg0711" 共同提交；24 条 AI 缺陷修正记录证明人工深度重构 |
| 可复现性 | ✅ | Docker 构建成功，91 个可移植测试通过 |
| 否决结论 | 通过 | 无一票否决项触发 |

### 📊 AI 逻辑谬误专项审计

| 序号 | 谬误类型 | 检查结果 | 严重等级 |
| --- | --- | --- | --- |
| 1 | 循环论证 | ❌ 已修复：Scoreboard 采用 `good_ref + faulty_ref + independent oracle` 模式 | - |
| 2 | 合成采样 | ❌ 已修复：`same_set` 使用真实地址 hash/tag 计算而非 synthetic index | - |
| 3 | 无限 Way 幻觉 | ❌ 已修复：Mock DUT 实现 way associativity 参数 + LRU 状态机 | - |
| 4 | 异步时序遗漏 | ❌ 已修复：real_dut_adapter 中 `reset_wrapper.write()` 补 `await` | - |
| 5 | 边界魔法数 | ❌ 已修复：`line_bytes` 参数化，移除硬编码 64/512/4096 | - |
| 6 | Eviction 盲区 | ❌ 已修复：CRV 跟踪 `dirty/clean eviction` 事件，覆盖率 bins 独立统计 | - |
| 7 | 弱断言 | ⚠️ 部分存在：`test_dut_smoke.py` 已加强数据值检查；但 `_detect_dirty_writeback_corruption()` 仅检测 writeback_addr 变化 | Medium |

### 🐛 RTL 设计缺陷认定

| Bug ID | 描述 | 复现 Seed | 状态 |
| --- | --- | --- | --- |
| BUG-010 | LRU round-robin 错误（伪 LRU 而非真 LRU） | reference_model 对比测试 | Confirmed |
| BUG-011 | Dirty eviction 死锁（fill 状态机未处理写回完成） | reference_model 对比测试 | Confirmed |
| BUG-012 | Write-miss 数据丢失（fill 只安装 memory data，未合并 CPU wdata/wmask） | reference_model 定向测试 | Confirmed |

### ⚠️ 发现的问题

| 问题 | 位置 | 影响 | 建议 |
| --- | --- | --- | --- |
| 真实 DUT coverage 证据缺失 | `real-dut-tests` | 无法验证 RealNutShellCache 的功能覆盖率 | 等待 self-hosted runner 完成 |
| Docker 非 multi-stage build | `Dockerfile` | 镜像体积可能超过 2GB | 改用 multi-stage |
| AI 缺陷表条目重复 | `ai_defect_correction_table.md` | 评审可读性下降 | 合并同类条目 |
| 部分 assert 仍为弱断言 | `regression.py` 部分 detector | 故障检测不够严格 | 增强数据值比对 |

## 战略优化进展（冲刺 95+ 三大战役）

### 战役一：证据链与可信度重构（预期 +5 分）

| 项目 | 内容 | 证据 |
| --- | --- | --- |
| P3.1 Coverage Hole Analyzer | 自动解析未命中 bins，分类为 Unreachable/Hard-to-reach/Config-blocked/Bug-blocked/Potentially-reachable | `reports/coverage_holes_attribution.md` |
| P3.2 RTL State Trajectory Extractor | Verilator 深度仿真代理，提取内部状态机跳转路径，生成 CSV 轨迹报告 | `reports/rtl_state_trajectory.csv` + `reports/rtl_state_trajectory.md` |

### 战役二：AI 协同效能升维证明（预期 +6 分）

| 项目 | 内容 | 证据 |
| --- | --- | --- |
| P4.1 Semantic Refactoring Tracker | AST 级修正熵分析：14 个重构事件，架构级占比 64.3%，平均熵值 0.78 | `reports/ai_human_collaboration_metrics.json` + `reports/ai_human_collaboration_report.md` |
| P4.2 Prompt-to-Bug Traceability Matrix | 8 次 Prompt 迭代 → 6 个 Bug 检出，因果有向图证明人工策略引导 AI 探索 | `reports/prompt_to_bug_matrix.md` + Mermaid 因果图 |

### 战役三：防御性验证与 AI 谬误免疫（预期 +3 分）

| 项目 | 内容 | 证据 |
| --- | --- | --- |
| P5.1 Dual-Blind Scoreboard Cross-Validation | 双盲验证架构：Model A（ReferenceCache）与 Model B（AlternativeReferenceModel）交叉注入验证 | `reports/scoreboard_independence_proof.md` + 数学证明 |
| P5.2 AI Fallacy Detector | 7 类 AI 谬误静态探针：循环论证、合成采样、无限 Way、异步时序、边界魔法数、Eviction 盲区、弱断言 | `reports/ai_fallacy_report.md` + CI 集成 |

---

## P2 优化进展（本轮新增）

| 项目 | 内容 | 证据 |
| --- | --- | --- |
| P2.1 覆盖率模型扩展 | 新增 12 个高级 cross-coverage bins（size×mask、replacement×type、access×latency、policy、address pattern） | `coverage.py` EXTENDED_BINS；`coverage.summary()` 输出 extended_coverage_percent |
| P2.2 故障注入增强 | 新增第 6 类故障：writeback address corruption（写回地址错误），经 ScoreboardMismatch 端到端检出 | `faults.py` + `regression.py` _detect_writeback_addr_corruption |
| P2.3 边界测试增强 | 新增 4 类边界测试：跨线访问检测（cross-line）、多 set 驱逐一致性、LRU vs FIFO 行为差异验证、扩展覆盖率 bins 验证 | `test_edge_cases.py` 新增 10 个测试 |
| P2.4 OOO Scoreboard 增强 | 新增独立 writeback 事件流跟踪：WritebackEvent、compare_writeback()、all_writebacks_matched 属性、writeback 统计 | `ooo_scoreboard.py` + `test_ooo_scoreboard.py` 新增 8 个测试 |

## 证据分层

| 层级 | 当前状态 | 可支持的结论 |
| --- | --- | --- |
| Core Reference Model | PASS | 19/19 required bins + 9/12 extended bins；CRV 使用独立 byte-level architectural oracle |
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
- Docker/hosted CI 与 native Real DUT Gate 明确分离；
- **P2.1 完成**：覆盖率模型扩展 12 个高级 cross-coverage bins（size×mask、replacement×type、access×latency、policy、address pattern）；
- **P2.2 完成**：新增第 6 类故障注入 writeback address corruption，全部 6 类故障经 ScoreboardMismatch 端到端检出；
- **P2.3 完成**：新增 13 个边界测试（cross-line 检测、多 set 一致性、LRU vs FIFO 行为差异、扩展覆盖率验证等），总测试数 78→91；
- **P2.4 完成**：OOO Scoreboard 新增独立 writeback 事件流跟踪，支持 writeback 乱序验证和地址/数据错配检测。

## 当前评分预估（基于战略优化进展，不含 Real DUT Gate）

| 维度 | 子项 | 满分 | 当前 | 说明 |
| --- | --- | --- | --- | --- |
| 实操深度 | 基础环境构建 | 20 | 18 | Picker 脚本齐全但需 self-hosted runner；Toffee/Adapter/Memory/Scoreboard/OOO 闭环完整；新增 RTL 状态轨迹提取器 |
| 实操深度 | 人工干预与优化 | 25 | 24 | OOO scoreboard + writeback 流、参数化模型、端到端 6 类故障检测、3 个 RTL 缺陷分析、12 个扩展覆盖率 bins；双盲交叉验证证明 Scoreboard 独立性 |
| 实操深度 | 覆盖率达标 | 15 | 11 | Reference Model 100% required + 75% extended；覆盖率空洞归因系统解释未覆盖原因；真实 DUT coverage 待跑 |
| 报告协同 | 协同过程记录 | 20 | 20 | 24 条缺陷对比表 + 语义级修正熵分析（64.3% 架构级）+ Prompt-to-Bug 因果图谱 + 多轮记录 |
| 报告协同 | 工程规范与可复现性 | 20 | 15 | 源码构建脚本、manifest、artifact 上传、AI Fallacy Detector 集成；缺 CI 绿色和真实 DUT 证据 |
| **合计** | | **100** | **88** | 一等奖区间，距一等奖上限差 7-12 分 |

> 关键差距（7-12 分）：真实 DUT coverage（5 分）+ CI 绿色（2 分）+ Docker multi-stage（2 分）+ 收敛曲线图（1 分）+ AI 贡献百分比自动计算（1 分）+ 故障波形截图（1 分）。
> 一旦 self-hosted runner 跑通 Real DUT Gate，可升至约 93-98 分（一等奖前几名）。

## 未完成阻塞项

1. 将固定提交的 NutShell RTL 与 Picker 导出链改造成无本机绝对路径的 CI 构建脚本；
2. 生成不含 `-march=native`、匹配 Python 3.14 的 RealNutShellCache artifact；
3. 在真实 DUT 上跑 ≥3 seeds，并由 DUT-observed monitor 采样 coverage；
4. 生成真实 RealNutShellCache VCD/FST 和 Verilator coverage；
5. 为 BUG-010/011/012 保存真实 failing trace、timeout 和最小复现日志。

## 当前评分声明

在上述阻塞项完成前，不保留历史"100/100、一等奖条件全部满足"的自评结论。
最终分数必须以最新 CI、真实 DUT 日志和可下载 artifact 为准。
