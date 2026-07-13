#!/usr/bin/env bash
# NutShell Cache verification runner for WSL2/Linux

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR
readonly PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
readonly XCOMM_SHORT_COMMIT="23ba5c4"
readonly XSPCOMM_CACHE_ROOT="${XSPCOMM_CACHE_ROOT:-${HOME}/.cache/nutshell-cache-verification}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "${ROOT_DIR}"

if ! "${PYTHON_BIN}" -m pytest --version >/dev/null 2>&1; then
    readonly VENV_DIR="${HOME}/.cache/nutshell-cache-verification/venv"
    echo "Creating verification environment at ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
    PYTHON_BIN="${VENV_DIR}/bin/python"
    "${PYTHON_BIN}" -m pip install \
        --index-url "${PIP_INDEX_URL}" \
        -e . \
        -r requirements-dev.txt
fi

XSPCOMM_ROOT="${XSPCOMM_ROOT:-${XSPCOMM_CACHE_ROOT}/xcomm-${XCOMM_SHORT_COMMIT}}"
PYTHON_ABI="$("${PYTHON_BIN}" -c \
    "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")"
if [[ ! -f "${XSPCOMM_ROOT}/build/.python-abi" ]] \
    || [[ "$(<"${XSPCOMM_ROOT}/build/.python-abi")" != "${PYTHON_ABI}" ]]; then
    echo "[1/5] Installing the Python-compatible xspcomm runtime"
    PYTHON_BIN="${PYTHON_BIN}" \
        bash scripts/install_xspcomm.sh
else
    echo "[1/5] Using cached xspcomm runtime for Python ${PYTHON_ABI}"
fi
export PYTHONPATH="${XSPCOMM_ROOT}/build/python${PYTHONPATH:+:${PYTHONPATH}}"
export LD_LIBRARY_PATH="${XSPCOMM_ROOT}/build/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
"${PYTHON_BIN}" -c "import xspcomm"

echo "[2/5] Checking Python style"
"${PYTHON_BIN}" -m ruff check src tests scripts tools
"${PYTHON_BIN}" -m ruff format --check src tests scripts tools

echo "[3/5] Running unit and real-DUT integration tests"
if [[ "${EMULATE_REAL_DUT_CPU:-0}" == "1" ]]; then
    if ! command -v qemu-x86_64 >/dev/null 2>&1; then
        echo "ERROR: EMULATE_REAL_DUT_CPU=1 requires qemu-x86_64 (qemu-user)." >&2
        exit 2
    fi
    DUT_PYTHON_BIN="$(command -v "${PYTHON_BIN}")"
    readonly DUT_PYTHON_BIN
    "${PYTHON_BIN}" -m pytest tests -v \
        --ignore=tests/test_real_dut_smoke.py \
        --cov=cache_vip --cov-report=term-missing
    if ! qemu-x86_64 -cpu max -d in_asm -D qemu-real-dut.log \
        "${DUT_PYTHON_BIN}" -m pytest tests/test_real_dut_smoke.py -v; then
        echo "QEMU failed; final translated instruction blocks:" >&2
        tail -120 qemu-real-dut.log >&2
        exit 1
    fi
else
    "${PYTHON_BIN}" -m pytest tests -v --cov=cache_vip --cov-report=term-missing
fi

echo "[4/5] Running core regression"
"${PYTHON_BIN}" -m cache_vip.regression --seeds 1,2,3,4,5 --count 1000

echo "[5/5] Generating real-DUT coverage evidence"
if [[ "${EMULATE_REAL_DUT_CPU:-0}" == "1" ]]; then
    qemu-x86_64 -cpu max "${DUT_PYTHON_BIN}" tools/gen_real_dut_coverage.py
else
    "${PYTHON_BIN}" tools/gen_real_dut_coverage.py
fi

echo "Verification completed successfully"
