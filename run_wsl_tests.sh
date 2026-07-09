#!/bin/bash
# WSL2 一键运行脚本：真实 NutShell Cache DUT 验证
# Usage: wsl -e bash -c "cd /mnt/d/UCagent && bash run_wsl_tests.sh"

set -e

echo "============================================================"
echo "NutShell Cache Verification - WSL2 Runner"
echo "============================================================"
echo ""

# Ensure dependencies
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "Installing pytest dependencies..."
    pip3 install --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple pytest pytest-asyncio 2>&1 | tail -3
fi

# Run all tests including real DUT
echo "[1/3] Running all unit tests (including real DUT smoke)..."
PYTHONPATH=src:. python3 -m pytest tests/ -v --asyncio-mode=auto 2>&1 | tail -20
echo ""

# Run core regression
echo "[2/3] Running core regression (5 seeds x 1000 txns)..."
PYTHONPATH=src:. python3 -c "
from cache_vip.regression import run_core_regression
r = run_core_regression(seeds=(1,2,3,4,5), count=1000)
print('Overall:', r['status'])
for c in r['crv']:
    print(f\"  {c['name']}: {c['status']} ({c['transactions']} txns, {c['coverage_percent']:.1f}%)\")
print('Coverage:', r['coverage']['coverage_percent'], '%')
print('Faults:', r['fault_detection'])
"
echo ""

# Generate real DUT coverage
echo "[3/3] Generating real DUT coverage report..."
PYTHONPATH=src:. python3 tools/gen_real_dut_coverage.py 2>&1 | tail -15
echo ""

echo "============================================================"
echo "All verification steps complete!"
echo "============================================================"
