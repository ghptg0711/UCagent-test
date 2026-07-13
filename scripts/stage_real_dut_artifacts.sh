#!/usr/bin/env bash
# Stage host-compatible RealNutShellCache libraries from an external build.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOT_DIR
readonly SOURCE_DIR="${REAL_DUT_ARTIFACT_DIR:?Set REAL_DUT_ARTIFACT_DIR to a compatible Picker build}"
readonly TARGET_DIR="${ROOT_DIR}/rtl/generated_real"

for artifact in _UT_RealNutShellCache.so libUTRealNutShellCache.so; do
    if [[ ! -f "${SOURCE_DIR}/${artifact}" ]]; then
        echo "ERROR: missing ${SOURCE_DIR}/${artifact}" >&2
        exit 2
    fi
    cp "${SOURCE_DIR}/${artifact}" "${TARGET_DIR}/${artifact}"
done

echo "Staged RealNutShellCache artifacts from ${SOURCE_DIR}"
