# 验收文档

## 1. 验收范围

本验收文档分为两级：

- Core 验收：不依赖真实 DUT，验证 Python reference model、generator、scoreboard、coverage、fault injection。
- DUT 验收：依赖 NutShell Cache Picker/Toffee 接入，验证真实 RTL 行为。

当前仓库已完成 Core 验收；DUT 验收需要真实信号映射和 Picker 产物。

## 2. Core 验收命令

在 WSL2 中执行：

```bash
cd /mnt/d/UCagent
.venv/bin/python -m compileall src tests
.venv/bin/python -m pytest tests
PYTHONPATH=src .venv/bin/python -m cache_vip.regression --seeds 1,2,3 --count 300 --report-dir reports
```

也可以安装后执行：

```bash
.venv/bin/python -m pip install -e .
.venv/bin/cache-vip-regress --seeds 1,2,3 --count 300 --report-dir reports
```

## 3. Core 通过标准

| 检查项 | 标准 | 当前结果 |
| --- | --- | --- |
| Python 语法 | `compileall` 无错误 | PASS |
| 单元测试 | 全部 pytest 通过 | PASS, 12 passed |
| 回归入口 | `status` 为 `PASS` | PASS |
| required coverage | 不低于 90% | PASS, 100% |
| fault detection | 4 类 fault 均检出 | PASS, 4/4 |
| 报告生成 | md/json 报告存在，包含 required bin hit table | PASS |

生成文件：

- `reports/core_regression_summary.md`
- `reports/core_regression_summary.json`

## 4. DUT Smoke 验收

接入真实 DUT 后，先执行最小闭环：

- reset 后单地址 read。
- 单地址 write 后 read。
- 同 line 连续 read，观察 miss 后 hit。
- partial write 后 full read。
- memory 固定短 latency。

通过标准：

- 无 X/Z 或非法响应。
- scoreboard 无 mismatch。
- monitor 能记录请求、响应、writeback。

## 5. DUT Directed 验收

必须覆盖：

- `ways + 1` 同 set 不同 tag。
- dirty eviction writeback。
- clean eviction。
- 1B/2B/4B/8B 访问。
- full/single/sparse mask。
- line boundary。
- memory long latency。
- backpressure。

通过标准：

- directed case 全通过。
- replacement、mask、latency、same-set coverage bin 非 0。
- dirty writeback 数据与参考模型一致。

## 6. DUT CRV 验收

推荐执行：

```bash
cache-vip-regress --seeds 1,2,3,4,5 --count 1000 --report-dir reports
```

如果已接入真实 DUT，应增加对应的 Toffee regression 命令，并记录：

- seed。
- transaction count。
- 失败事务序号。
- mismatch 信息。
- 波形路径。

通过标准：

- 至少 3 个 seed 稳定通过。
- 功能覆盖率不低于 90%。
- 失败可复现。

## 7. Fault Injection 验收

Core 已完成以下负向验收：

- read data bit flip。
- partial write mask drop。
- dirty writeback data corruption。
- response order swap。

DUT 接入后，建议把 fault injection 放在 memory agent 或 response monitor 边界，证明真实 testbench 也能检出同类问题。

## 8. 最终提交检查

- [ ] `docs/contest_statement.md` 存在。
- [ ] `docs/overall_solution.md` 存在。
- [ ] `docs/acceptance_document.md` 存在。
- [ ] `docs/verification_report.md` 已更新。
- [ ] `docs/final_checklist.md` 已执行。
- [ ] `reports/core_regression_summary.md/json` 已生成。
- [ ] 不提交 `.venv/`、`.pytest_cache/`、`__pycache__/`、`*.egg-info/`。
- [ ] 如已接入 DUT，真实 RTL 覆盖率和 bug 记录已更新。
