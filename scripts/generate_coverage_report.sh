#!/bin/bash
# Generate Verilator coverage artifacts and a machine-readable summary.
set -euo pipefail

COVERAGE_DIR="reports/verilator_coverage"
mkdir -p "${COVERAGE_DIR}/annotated"

echo "=== Coverage Report Generation ==="

if [ ! -f "${COVERAGE_DIR}/coverage.dat" ]; then
  echo "ERROR: ${COVERAGE_DIR}/coverage.dat not found"
  exit 1
fi

echo "[1/3] Annotating coverage"
verilator_coverage --annotate "${COVERAGE_DIR}/annotated" "${COVERAGE_DIR}/coverage.dat" || true

echo "[2/3] Writing LCOV info"
verilator_coverage --write-info "${COVERAGE_DIR}/coverage.info" "${COVERAGE_DIR}/coverage.dat" || true

echo "[3/3] Summarizing coverage"
python3 scripts/summarize_coverage.py

echo "=== Coverage Report Complete ==="
