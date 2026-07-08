"""Report writing and markdown formatting for cache regression results."""

from __future__ import annotations

import json
from pathlib import Path


def write_reports(report_dir: Path, summary: dict[str, object]) -> None:
    """Write JSON and Markdown regression summaries."""
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "core_regression_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (report_dir / "core_regression_summary.md").write_text(format_markdown(summary), encoding="utf-8")


def format_markdown(summary: dict[str, object]) -> str:
    """Format either core or enhanced regression summary as Markdown."""
    lines = [
        "# Regression Summary",
        "",
        f"Status: `{summary['status']}`",
        "",
    ]

    if "core_regression" in summary:
        lines.extend(_format_enhanced_markdown(summary))
    else:
        lines.extend(_format_core_markdown(summary))
    lines.append("")
    return "\n".join(lines)


def _format_core_markdown(summary: dict[str, object]) -> list[str]:
    coverage = summary["coverage"]
    faults = summary["fault_detection"]
    crv = summary["crv"]
    lines = [
        "## Coverage",
        "",
        f"- Required bin coverage: `{coverage['coverage_percent']}%`",
        f"- Covered bins: `{coverage['covered_bins']}/{coverage['total_bins']}`",
        f"- Missing bins: `{', '.join(coverage['missing']) if coverage['missing'] else 'none'}`",
        "",
        "## Fault Detection",
        "",
    ]
    for name, detected in faults.items():
        lines.append(f"- {name}: `{'detected' if detected else 'missed'}`")
    lines.extend(["", "## Required Bin Counts", "", "| Bin | Hits |", "| --- | ---: |"])
    for name, hits in coverage["bins"].items():
        lines.append(f"| `{name}` | {hits} |")
    lines.extend(["", "## CRV", ""])
    for item in crv:
        lines.append(
            f"- {item['name']}: `{item['transactions']}` transactions, "
            f"status `{item['status']}`, coverage `{item['coverage_percent']}%`"
        )
    return lines


def _format_enhanced_markdown(summary: dict[str, object]) -> list[str]:
    lines: list[str] = []

    cov_summary = summary.get("coverage_summary", {})
    total_bins = len(cov_summary)
    covered_bins = sum(1 for h in cov_summary.values() if h > 0)
    cov_pct = (covered_bins / total_bins * 100.0) if total_bins else 100.0
    lines.extend([
        "## Coverage Summary",
        "",
        f"- Bin coverage: `{cov_pct:.1f}%` ({covered_bins}/{total_bins})",
        "",
        "| Bin | Total Hits |",
        "| --- | ---: |",
    ])
    for name, hits in cov_summary.items():
        lines.append(f"| `{name}` | {hits} |")

    lines.extend(["", "## Core Regression", ""])
    for item in summary.get("core_regression", []):
        lines.append(
            f"- {item['name']}: `{item['transactions']}` txns, "
            f"status `{item['status']}`, coverage `{item['coverage_percent']}%`"
        )

    dut_results = summary.get("dut_regression", [])
    if dut_results:
        lines.extend(["", "## DUT Regression", ""])
        for item in dut_results:
            lines.append(
                f"- {item['name']}: `{item['transactions']}` txns, "
                f"status `{item['status']}`, coverage `{item['coverage_percent']}%`"
            )

    faults = summary.get("fault_detection", {})
    if faults:
        lines.extend(["", "## Fault Detection", ""])
        for name, detected in faults.items():
            lines.append(f"- {name}: `{'detected' if detected else 'missed'}`")

    return lines
