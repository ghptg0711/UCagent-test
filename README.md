# NutShell Cache 自动化验证（基于 UCAgent）

![Verification](https://github.com/ghptg0711/UCagent/actions/workflows/verification.yml/badge.svg)

## Overview

本项目基于 **UCAgent**（AI 驱动验证智能体）完成对开源 RISC-V 处理器 [NutShell](https://github.com/OpenXiangShan/NutShell) 中 **Cache 子系统**的自动化功能验证。

验证闭环采用 **Picker / Toffee** 框架搭建，核心验证组件与 DUT 适配层解耦，支持在纯 Python 环境下运行单元回归，也可在 WSL2 环境下对接真实 NutShell Cache DUT 进行端到端验证。

验证平台包含以下关键能力：

- **参考模型（Reference Model）**：位级精确的 Cache 行为模型，支持读写命中/缺失、替换、脏回写、部分写掩码合并等语义。
- **激励生成器（Generator）**：提供定向用例与约束随机（CRV）流，覆盖替换、RAW 冒险、行边界、部分写、跨偏移、非缓存访问等场景。
- **计分板（Scoreboard）**：逐事务比对 DUT 与参考模型响应，检测数据错配、事务序错乱等故障。
- **覆盖率收集器（Coverage）**：功能覆盖率建模，含命中/缺失、脏/干净替换、延迟档位、同 set 访问等 bins。
- **故障注入（Faults）**：注入读数据位翻转、写掩码丢弃、脏回写破坏、响应序交换等故障，验证计分板检出能力。
- **真实 DUT 适配器（Real DUT Adapter）**：通过 Picker 生成的 Python 绑定对接 Verilator 编译的真实 NutShell Cache DUT。

## Quick Start

```bash
# 环境要求：Python 3.10+, WSL2 (Ubuntu), Verilator 5.032
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest pytest-asyncio

# 运行测试
python -m pytest tests/ -v --asyncio-mode=auto

# 运行核心回归
PYTHONPATH=src python -m cache_vip.regression

# 运行真实 DUT 测试（需 WSL2）
PYTHONPATH=src:. python -m pytest tests/test_real_dut_smoke.py -v --asyncio-mode=auto
```

## Project Structure

```
.
├── src/cache_vip/        # 验证组件
│   ├── reference_model.py    # 参考模型
│   ├── generator.py          # 激励生成器
│   ├── scoreboard.py         # 计分板
│   ├── coverage.py           # 覆盖率收集器
│   ├── faults.py             # 故障注入
│   ├── regression.py         # 回归入口
│   ├── toffee_adapter.py     # Toffee 适配层
│   ├── real_dut_adapter.py   # 真实 DUT 适配器
│   ├── memory_agent.py       # 内存代理
│   └── transactions.py       # 事务定义
├── tests/                # 测试用例（Mock DUT + real DUT smoke）
├── docs/                 # 文档（方案设计、验收计划、验证报告等）
├── reports/              # 验证报告（回归摘要、覆盖率、缺陷跟踪）
├── configs/              # 信号映射配置（signal_map*.yaml）
├── scripts/              # Verilator 构建、仿真和覆盖率脚本
└── rtl/                  # RTL 和 Picker 生成产物
    ├── dut_gen/          # 预编译 Verilog RTL
    └── generated_real/   # Picker 生成的 Python DUT 封装
```

注意：NutShell Cache RTL 以预编译 Verilog 形式引入（非 Chisel/Scala 源码）。
原始源码来自 NutShell 项目的 Cache 子系统，通过 Chisel 编译为 Verilog 后提交，
以确保验证环境的可复现性。

## Verification Results

| 指标 | 结果 |
| --- | --- |
| 功能覆盖率 | **100%**（19/19 bins） |
| 故障检出 | **5/5** 全部检出 |
| 单元测试 | 详见 CI 与本地 pytest 日志 |
| CRV 回归 | 多 seed 约束随机回归，详见 `reports/core_regression_summary.md` |

详细验证数据见 `reports/coverage_summary.md` 与 `reports/core_regression_summary.md`。

## CI

项目通过 GitHub Actions 持续集成（见 `.github/workflows/verification.yml`），包含两个作业：

- **unit-tests**：在标准 Ubuntu Runner 上运行单元测试与核心回归，不依赖 WSL2。
- **real-dut-tests**：运行真实 DUT 冒烟测试，需要 Picker/Verilator 构建产物。

## License

本项目遵循 [Apache License 2.0](LICENSE)。
