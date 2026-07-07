# 自行验收计划

## 1. 环境验收

在 WSL2 中确认：

```bash
python --version
python -m pip show pytest pytoffee
picker --version || true
verilator --version
```

验收通过标准：

- Python、pytest、Toffee、Picker、Verilator 可用。
- NutShell Cache RTL 能独立编译。
- Picker 能生成可被 Python 加载的仿真模型。

## 2. 仓库静态验收

```bash
python -m compileall src tests
python -m pytest tests
PYTHONPATH=src python -m cache_vip.regression --seeds 1,2,3 --count 200 --report-dir reports
```

通过标准：

- 所有 Python 文件无语法错误。
- DUT 无关单元测试全通过。
- Core regression CLI 生成 `reports/core_regression_summary.md/json`。
- 根目录存在 Apache 2.0 `LICENSE`。

## 3. DUT Smoke 验收

建议先跑 5 个最小 case：

- reset 后单地址 read，期望从 memory fill。
- 单地址 write 后 read，期望读回写入数据。
- 同一 cache line 多次 read，第一次 miss，后续 hit。
- 同一 cache line partial write 后 full read。
- memory 固定 1 到 3 cycle latency。

通过标准：

- 无 X/Z 响应。
- Scoreboard 无 mismatch。
- Monitor 能导出请求/响应日志。

## 4. Directed Corner 验收

必须覆盖：

- 同 set `ways + 1` 个 tag，触发替换。
- dirty line eviction 后重新读回，验证写回正确。
- byte/half/word/doubleword mask merge。
- line 边界附近访问。
- memory response 长延迟和 backpressure。

通过标准：

- directed case 全部通过。
- 至少观察到 clean eviction 和 dirty eviction。
- 覆盖率报告中 replacement、mask、latency bin 非 0。

## 5. CRV 回归验收

建议命令格式：

```bash
python -m pytest tests/test_nutshell_cache_regression.py --seed=1 --count=1000
python -m pytest tests/test_nutshell_cache_regression.py --seed=2 --count=1000
python -m pytest tests/test_nutshell_cache_regression.py --seed=3 --count=1000
```

通过标准：

- 三个 seed 均通过。
- functional coverage 大于等于 90%。
- 失败时能输出 seed、事务序号、地址、期望值、实际值。

## 6. Fault Injection 验收

必须证明以下负向 case 能失败：

- read data bit flip。
- partial write mask drop。
- dirty writeback data corruption。
- response order swap。

通过标准：

- 每个 fault case 都被 Scoreboard 捕获。
- 报告中保留错误摘要、复现 seed、最小复现序列。

## 7. 最终提交验收

最终提交前检查：

```bash
git status --short
python -m compileall src tests
python -m pytest tests
```

提交包应包含：

- 完整源码。
- `docs/verification_report.md` 或按模板完成的报告。
- `reports/coverage_summary.*`。
- `reports/core_regression_summary.md/json`。
- `reports/bug_tracker.md`。
- `reports/ai_collaboration_log.md`。
