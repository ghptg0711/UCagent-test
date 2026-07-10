# 下一轮优化 AI 提示词

## 任务背景

你是一名验证工程师，正在继续完善 NutShell Cache 验证环境。当前状态：

**33 个测试全部通过，核心覆盖率 100%（19/19 bins），4 类 fault 全部检出。Toffee adapter 和 memory agent 已在 mock DUT 上验证通过。

---

## 当前状态回顾

### 已完成

- ✅ P0-1: DUT smoke（mock DUT 上 7 个测试通过）
- ✅ P0-2: ToffeeMemoryAgent（fill, writeback, latency, backpressure）
- ✅ P0-3: 参数化 Cache 策略（LRU/FIFO/Random + write-allocate/no-write-allocate）
- ✅ P1-1: 14 个 directed cases（LRU 检查、RAW 依赖、边界访问、uncached 等）
- ✅ P1-2: 增强回归（10 seeds x 1000 txns + per-seed coverage + repro window）

### 核心文件清单

| 文件 | 状态 | 说明 |
| --- | --- | --- |
| `src/cache_vip/transactions.py` | ✅ 完成 | 事务模型（CacheTxn, CacheResponse） |
| `src/cache_vip/reference_model.py` | ✅ 完成 | 参考模型（参数化策略） |
| `src/cache_vip/scoreboard.py` | ✅ 完成 | Scoreboard（比对 + fault injection） |
| `src/cache_vip/generator.py` | ✅ 完成 | 激励生成器（12+ directed cases） |
| `src/cache_vip/coverage.py` | ✅ 完成 | 覆盖率收集器（19 bins） |
| `src/cache_vip/memory_agent.py` | ✅ 完成 | 内存 agent（Scripted + Toffee） |
| `src/cache_vip/fault_injection.py` | ✅ 完成 | 故障注入（4 类 fault） |
| `src/cache_vip/toffee_adapter.py` | ✅ 完成 | Toffee 适配器（reset/drive/sample） |
| `src/cache_vip/regression.py` | ✅ 完成 | 回归入口（增强版） |
| `configs/signal_map.yaml` | ✅ 完成 | 信号映射配置 |
| `tests/mock_dut.py` | ✅ 完成 | Mock DUT 模型 |
| `tests/test_dut_smoke.py` | ✅ 完成 | DUT smoke 测试（7 个） |
| `tests/test_directed_cases.py` | ✅ 完成 | Directed cases 测试（14 个） |

---

## 下一轮任务

### 任务 1：真实 DUT 接入（最高优先级）

**目标：** 将 mock DUT 替换为真实 NutShell Cache Picker 生成的模型

**输入：**
- 真实 NutShell Cache RTL 路径
- Picker 工具已安装

**步骤：**

1. **生成 DUT Python 模型
```bash
picker generate \
  --top <cache_top_module_name> \
  --rtl <rtl_files> \
  --out <output_dir>
```
记录生成命令和输出路径

2. **分析 DUT 接口信号
- 列出所有 CPU 侧信号（req/resp）
- 列出所有 Memory 侧信号（req/resp）
- 确认信号名、位宽、方向

3. **更新 signal_map.yaml**
- 根据真实信号名更新配置文件
- 注意信号位宽匹配
- 注意字节序（小端/大端）

4. **验证 DUT smoke 测试**
- 运行 `tests/test_dut_smoke.py` 对接真实 DUT
- 逐个修复信号映射问题
- 确保 7 个 smoke 测试全部通过

5. **记录问题和修复
- 记录每个问题的现象、根因、修复方案
- 更新 bug_tracker.md

**验收标准：**
- 真实 DUT smoke 测试全部通过（至少 5/7）
- signal_map.yaml 包含完整信号映射
- 有波形/日志证据

---

### 任务 2：真实 DUT directed cases 运行

**目标：** 在真实 DUT 上运行所有 directed cases

**输入：**
- 已通过 smoke 的 DUT 适配器
- 14 个 directed cases

**步骤：**

1. **逐个运行 directed cases**
```bash
python -m pytest tests/test_directed_cases.py -v
```

2. **调试失败用例**
- 记录失败用例名称
- 分析失败原因（DUT 行为 vs 参考模型）
- 判断是 DUT bug 还是验证环境问题

3. **修复适配层问题**
- 如果是适配层问题，修复 toffee_adapter.py
- 如果是参考模型策略不匹配，参数化调整
- 如果是 DUT bug，记录到 bug_tracker

4. **生成 DUT 覆盖率**
- 接入 Toffee monitor 收集信号
- 导出 DUT 实测覆盖率
- 与 core coverage 对比

**验收标准：**
- 至少 10 个以上 directed cases 通过
- 失败用例有详细分析记录
- DUT 覆盖率有初步数据

---

### 任务 3：CRV 回归在真实 DUT 上

**目标：** 在真实 DUT 上运行 CRV 回归

**输入：**
- 已通过 smoke 的 DUT
- 增强回归脚本

**步骤：**

1. **小规模 DUT CRV 运行**
```bash
PYTHONPATH=src python -c "
from cache_vip.regression import run_enhanced_regression
import pathlib
run_enhanced_regression(
    dut_seeds=[1, 2, 3],
    dut_count=200,
    report_dir=pathlib.Path('reports/dut_regression'),
)
"
```

2. **性能优化**
- 如果运行慢，减少 txn 数或 seed 数
- 并行运行多个 seeds

3. **覆盖率分析**
- 对比 core vs DUT 覆盖率
- 找出 DUT 上未覆盖的 bins
- 补充 directed case 填补

4. **bug 复现**
- 如果发现 DUT bug，用 repro window 最小化
- 记录 bug 详细信息

**验收标准：**
- DUT CRV 3 seeds x 200 txns 稳定运行
- 有 DUT 覆盖率数据
- 发现的 bug 有详细记录

---

### 任务 4：文档和报告完善

**目标：** 完善所有提交文档，达到答辩水平

**步骤：**

1. **更新 verification_report.md**
- 补充真实 DUT 测试结果
- 补充 DUT 覆盖率数据
- 补充 bug 列表和分析
- 补充波形截图路径

2. **完善 AI 协作记录**
- 记录每轮 AI 提示词
- 记录 AI 生成的初稿和问题
- 记录人工 review 和修改点
- 记录 bug 修复前后对比

3. **创建最终检查清单**
```markdown
# Final Checklist
## 代码
- [ ] 所有测试通过
- [ ] 覆盖率达标
- [ ] 无遗留 TODO/FIXME
- [ ] 代码风格一致
## 文档
- [ ] 赛题说明完整
- [ ] 整体方案完整
- [ ] 验收文档完整
- [ ] 验证报告完整
- [ ] 覆盖率报告完整
- [ ] Bug 记录完整
- [ ] AI 协作记录完整
## 可复现
- [ ] WSL2 环境可复现
- [ ] 命令可复制运行
- [ ] seed 固定，结果稳定
```

4. **准备答辩材料**
- 核心亮点总结
- 技术难点和创新点
- 数据支撑（覆盖率、bug 数、测试数）

**验收标准：**
- 所有文档路径存在且内容完整
- 最终检查清单 90% 以上勾选

---

## 约束条件

1. **所有测试必须在 WSL2 中执行**
2. **核心验证组件保持 DUT-independent**
3. **协议适配层隔离在 toffee_adapter.py 中**
4. **异步编程使用 async/await**
5. **同一 seed 和配置下结果稳定可复现**

---

## 执行命令汇总

```bash
# 进入 WSL2
wsl -d Ubuntu
cd /mnt/d/UCagent
source .venv/bin/activate

# 全量测试
python -m pytest tests/ -v

# 核心回归
PYTHONPATH=src python -m cache_vip.regression --seeds 1,2,3,4,5 --count 500 --report-dir reports

# 增强回归（10 seeds x 1000 txns）
PYTHONPATH=src python -c "
from cache_vip.regression import run_enhanced_regression
import pathlib
run_enhanced_regression(
    core_seeds=range(1, 11),
    core_count=1000,
    report_dir=pathlib.Path('reports/enhanced'),
)
"
```

---

## 交付物清单（最终）

| 文件 | 描述 | 状态 |
| --- | --- | --- |
| `docs/contest_statement.md` | 赛题说明 | ✅ |
| `docs/overall_solution.md` | 整体方案 | ✅ |
| `docs/acceptance_document.md` | 验收文档 | ✅ |
| `docs/verification_report.md` | 验证报告 | ⏳ 待补充 DUT 数据 |
| `docs/score_90_optimization_plan.md` | 优化路线 | ✅ |
| `docs/final_checklist.md` | 最终检查清单 | ⏳ 待创建 |
| `reports/coverage_summary.md` | 覆盖率报告 | ✅ |
| `reports/dut_smoke_result.md` | DUT smoke 结果 | ✅ (mock) |
| `reports/bug_tracker.md` | Bug 记录 | ⏳ 待补充真实 bug |
| `reports/ai_collaboration_log.md` | AI 协作记录 | ⏳ 待完善 |
| `reports/core_regression_summary.md` | 核心回归摘要 | ✅ |

---

## 评分路线图

```
当前状态（~70-75分）
    │
    ▼
接入真实 DUT smoke（~80分）
    │
    ▼
DUT directed cases + 覆盖率（~85分）
    │
    ▼
DUT CRV 回归 + bug 发现（~90分）
    │
    ▼
文档完善 + 答辩准备（~95分）
```
