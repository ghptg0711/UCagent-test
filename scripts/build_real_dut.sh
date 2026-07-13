#!/usr/bin/env bash
# Build host-compatible Picker bindings from generated RealNutShellCache RTL.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOT_DIR
readonly RTL_DIR="${REAL_DUT_RTL_DIR:-${ROOT_DIR}/rtl/generated_real_src}"
readonly BUILD_DIR="${REAL_DUT_BUILD_DIR:-${ROOT_DIR}/build/real_dut}"
readonly TARGET_DIR="${ROOT_DIR}/rtl/generated_real"
readonly PICKER_BIN="${PICKER_BIN:-picker}"

if ! command -v "${PICKER_BIN}" >/dev/null 2>&1; then
    echo "ERROR: Picker is required; set PICKER_BIN to its executable" >&2
    exit 2
fi
if [[ ! -d "${RTL_DIR}" ]]; then
    echo "ERROR: generated RTL is missing; run tools/generate_real_cache_rtl.sh" >&2
    exit 2
fi

filelist="${BUILD_DIR}/real_dut_filelist.f"
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"
find "${RTL_DIR}" -maxdepth 1 -type f \( -name '*.v' -o -name '*.sv' \) \
    -print | sort >"${filelist}"
if [[ ! -s "${filelist}" ]]; then
    echo "ERROR: no Verilog/SystemVerilog files found in ${RTL_DIR}" >&2
    exit 2
fi

"${PICKER_BIN}" export \
    --fs "${filelist}" \
    --sname RealNutShellCache \
    --tname RealNutShellCache \
    --tdir "${BUILD_DIR}/picker" \
    --lang python \
    --sim verilator \
    --coverage \
    --wave_file_name RealNutShellCache.fst \
    --cflag "-march=x86-64 -mtune=generic" \
    --copy_xspcomm_lib false \
    --autobuild true

extension="$(find "${BUILD_DIR}/picker" -type f -name '_UT_RealNutShellCache.so' -print -quit)"
simulator="$(find "${BUILD_DIR}/picker" -type f -name 'libUTRealNutShellCache.so' -print -quit)"
if [[ -z "${extension}" || -z "${simulator}" ]]; then
    echo "ERROR: Picker build completed without the expected Python libraries" >&2
    exit 2
fi

cp "${extension}" "${TARGET_DIR}/_UT_RealNutShellCache.so"
cp "${simulator}" "${TARGET_DIR}/libUTRealNutShellCache.so"
echo "Built host-compatible RealNutShellCache libraries in ${TARGET_DIR}"
