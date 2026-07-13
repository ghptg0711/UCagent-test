#!/usr/bin/env bash
# Generate RealNutShellCache SystemVerilog from the pinned NutShell source.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOT_DIR
readonly NUTSHELL_COMMIT="041f694965728ea183a0622daa1734002bf4621e"
readonly NUTSHELL_DIR="${NUTSHELL_DIR:-${ROOT_DIR}/NutShell}"
readonly OUTPUT_DIR="${REAL_DUT_RTL_DIR:-${ROOT_DIR}/rtl/generated_real_src}"
readonly MILL_BIN="${MILL_BIN:-mill}"
readonly SCALA_VERSION="2.13.14"

if [[ ! -d "${NUTSHELL_DIR}/.git" ]]; then
    echo "ERROR: clone the pinned NutShell repository at ${NUTSHELL_DIR}" >&2
    exit 2
fi
if [[ "$(git -C "${NUTSHELL_DIR}" rev-parse HEAD)" != "${NUTSHELL_COMMIT}" ]]; then
    echo "ERROR: NutShell must be checked out at ${NUTSHELL_COMMIT}" >&2
    exit 2
fi
if ! command -v "${MILL_BIN}" >/dev/null 2>&1; then
    echo "ERROR: Mill 0.11.7 is required" >&2
    exit 2
fi

export NOOP_HOME="${NUTSHELL_DIR}"
export MILL_JVM_OPTS="${MILL_JVM_OPTS:--Xmx4G}"

git -C "${NUTSHELL_DIR}" -c http.version=HTTP/1.1 \
    submodule update --init --force --depth=1 difftest

(cd "${NUTSHELL_DIR}" && "${MILL_BIN}" --no-server --disable-ticker generator.compile)
classpath_json="$(mktemp)"
trap 'rm -f "${classpath_json}"' EXIT
(cd "${NUTSHELL_DIR}" && "${MILL_BIN}" --no-server --disable-ticker \
    show generator.runClasspath) >"${classpath_json}"

runtime_cp="$(python3 - "${classpath_json}" <<'PY'
import json
import sys

items = json.load(open(sys.argv[1], encoding="utf-8"))["value"]
print(":".join(item.split(":", 3)[-1] if item.startswith(("qref:", "ref:")) else item for item in items))
PY
)"

find_jar() {
    local pattern="$1"
    local jar
    jar="$(find "${HOME}/.cache/coursier" -type f -name "${pattern}" -print -quit)"
    if [[ -z "${jar}" ]]; then
        echo "ERROR: dependency jar not found: ${pattern}" >&2
        exit 2
    fi
    printf '%s' "${jar}"
}

compiler="$(find_jar "scala-compiler-${SCALA_VERSION}.jar")"
library="$(find_jar "scala-library-${SCALA_VERSION}.jar")"
reflect="$(find_jar "scala-reflect-${SCALA_VERSION}.jar")"
plugin="$(find_jar "chisel-plugin_${SCALA_VERSION}-*.jar")"
classes_dir="${NUTSHELL_DIR}/out/manual-realcache/classes"
rm -rf "${classes_dir}"
mkdir -p "${classes_dir}"

java -cp "${compiler}:${library}:${reflect}" scala.tools.nsc.Main \
    -cp "${runtime_cp}" \
    -d "${classes_dir}" \
    -Xplugin:"${plugin}" \
    -Ymacro-annotations \
    "${ROOT_DIR}/tools/RealCacheMain.scala"

rm -rf "${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}"
java -cp "${classes_dir}:${runtime_cp}" top.RealCacheMain \
    --target-dir "${OUTPUT_DIR}" \
    --split-verilog

find "${OUTPUT_DIR}" -maxdepth 1 -type f -print | sort
