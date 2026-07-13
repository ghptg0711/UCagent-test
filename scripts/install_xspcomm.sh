#!/usr/bin/env bash
# Build the Picker xspcomm runtime for the active WSL/Linux Python ABI.

set -euo pipefail

readonly XCOMM_COMMIT="23ba5c47310a74dab1567a4ca54ad85dec4512cb"
readonly XCOMM_SHORT_COMMIT="23ba5c4"
readonly XCOMM_PRIMARY_URL="https://gitlink.org.cn/XS-MLVP/xcomm.git"
readonly XCOMM_FALLBACK_URL="https://github.com/XS-MLVP/xcomm.git"
readonly CACHE_ROOT="${XSPCOMM_CACHE_ROOT:-${HOME}/.cache/nutshell-cache-verification}"
readonly SOURCE_DIR="${CACHE_ROOT}/xcomm-${XCOMM_SHORT_COMMIT}"
readonly PYTHON_BIN="${PYTHON_BIN:-python3}"
readonly BUILD_LOG="${CACHE_ROOT}/xcomm-${XCOMM_SHORT_COMMIT}.build.log"
PYTHON_ROOT="$("${PYTHON_BIN}" -c 'import sys; print(sys.prefix)')"
readonly PYTHON_ROOT

install_system_dependencies() {
    local packages=(build-essential cmake swig python3-dev git)
    if [[ "$(id -u)" == "0" ]]; then
        apt-get update
        DEBIAN_FRONTEND=noninteractive apt-get install -y "${packages[@]}"
    elif sudo -n true >/dev/null 2>&1; then
        sudo apt-get update
        sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y "${packages[@]}"
    else
        echo "ERROR: missing native build dependencies." >&2
        echo "Install them with: sudo apt-get install ${packages[*]}" >&2
        exit 2
    fi
}

has_build_dependencies() {
    command -v cmake >/dev/null 2>&1 \
        && command -v c++ >/dev/null 2>&1 \
        && command -v swig >/dev/null 2>&1 \
        && command -v git >/dev/null 2>&1 \
        && "${PYTHON_BIN}" -c \
            "import os, sysconfig; assert os.path.isfile(os.path.join(sysconfig.get_path('include'), 'Python.h'))" \
            >/dev/null 2>&1
}

fetch_source() {
    if [[ -d "${SOURCE_DIR}/.git" ]] \
        && [[ "$(git -C "${SOURCE_DIR}" rev-parse HEAD)" == "${XCOMM_COMMIT}" ]]; then
        return
    fi

    rm -rf "${SOURCE_DIR}"
    mkdir -p "${CACHE_ROOT}"
    if ! git clone --depth=1 "${XCOMM_PRIMARY_URL}" "${SOURCE_DIR}"; then
        echo "Domestic mirror unavailable; falling back to the official repository."
        rm -rf "${SOURCE_DIR}"
        git clone --depth=1 "${XCOMM_FALLBACK_URL}" "${SOURCE_DIR}"
    fi

    if [[ "$(git -C "${SOURCE_DIR}" rev-parse HEAD)" != "${XCOMM_COMMIT}" ]]; then
        git -C "${SOURCE_DIR}" fetch --depth=1 origin "${XCOMM_COMMIT}"
        git -C "${SOURCE_DIR}" checkout --detach "${XCOMM_COMMIT}"
    fi
}

if ! has_build_dependencies; then
    install_system_dependencies
fi

fetch_source
rm -rf "${SOURCE_DIR}/build"
if ! {
    BUILD_XSPCOMM_SWIG=python cmake \
        -S "${SOURCE_DIR}" \
        -B "${SOURCE_DIR}/build" \
        -DCMAKE_BUILD_TYPE=Release \
        -DPython3_EXECUTABLE="${PYTHON_BIN}" \
        -DPython3_ROOT_DIR="${PYTHON_ROOT}"
    cmake --build "${SOURCE_DIR}/build" --parallel "${XSPCOMM_BUILD_JOBS:-2}"
} >"${BUILD_LOG}" 2>&1; then
    echo "ERROR: xspcomm build failed; last 80 log lines:" >&2
    tail -80 "${BUILD_LOG}" >&2
    exit 1
fi

export PYTHONPATH="${SOURCE_DIR}/build/python${PYTHONPATH:+:${PYTHONPATH}}"
export LD_LIBRARY_PATH="${SOURCE_DIR}/build/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
"${PYTHON_BIN}" -m xspcomm.info --version
"${PYTHON_BIN}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" \
    >"${SOURCE_DIR}/build/.python-abi"

echo "xspcomm runtime installed at ${SOURCE_DIR}"
echo "Set XSPCOMM_ROOT=${SOURCE_DIR} when invoking the verification runner."
