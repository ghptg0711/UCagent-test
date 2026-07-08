#!/usr/bin/env python3
"""Summarize Verilator code coverage percentages.

The script prefers LCOV-style `coverage.info` because it is emitted by
`verilator_coverage --write-info`. It falls back to LCOV-like records in
`coverage.dat` when the info file is unavailable.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


COVERAGE_DIR = Path("reports/verilator_coverage")
INFO_PATH = COVERAGE_DIR / "coverage.info"
DAT_PATH = COVERAGE_DIR / "coverage.dat"
SUMMARY_PATH = COVERAGE_DIR / "coverage_summary.json"


def _pct(hit: int, total: int) -> float:
    return round(hit * 100.0 / total, 1) if total else 0.0


def parse_lcov(path: Path) -> dict[str, dict[str, float | int]]:
    line_total = line_hit = 0
    branch_total = branch_hit = 0

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if raw.startswith("DA:"):
            line_total += 1
            _, count = raw[3:].split(",", 1)
            if int(count) > 0:
                line_hit += 1
        elif raw.startswith("BRDA:"):
            branch_total += 1
            taken = raw.rsplit(",", 1)[-1]
            if taken not in ("0", "-"):
                branch_hit += 1

    return {
        "line": {"hit": line_hit, "total": line_total, "pct": _pct(line_hit, line_total)},
        "branch": {"hit": branch_hit, "total": branch_total, "pct": _pct(branch_hit, branch_total)},
    }


def main() -> None:
    source = INFO_PATH if INFO_PATH.exists() else DAT_PATH
    if not source.exists():
        raise SystemExit(f"ERROR: no coverage file found at {INFO_PATH} or {DAT_PATH}")

    result = parse_lcov(source)
    result["metadata"] = {
        "tool": "Verilator",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source_file": str(source),
        "dut_file": "rtl/dut_gen/NutShellCache.v",
    }

    COVERAGE_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print("=" * 60)
    print("Verilator Code Coverage Summary")
    print("=" * 60)
    print(f"Source: {source}")
    print("Tool: Verilator")
    print(f"Line Coverage:   {result['line']['hit']}/{result['line']['total']} ({result['line']['pct']}%)")
    print(f"Branch Coverage: {result['branch']['hit']}/{result['branch']['total']} ({result['branch']['pct']}%)")
    print(f"Saved to: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
