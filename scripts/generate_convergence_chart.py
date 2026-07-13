"""Coverage Convergence Chart Generator - Generate 10-seed coverage trend visualization.

This script runs regression with 10 seeds and generates:
1. Coverage convergence CSV data
2. ASCII bar chart showing coverage progression per seed
3. Markdown report with convergence analysis

Example usage:
    python scripts/generate_convergence_chart.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cache_vip.regression import run_core_regression
from cache_vip.reference_model import CacheParams


def generate_convergence_data(
    num_seeds: int = 10,
    count_per_seed: int = 500,
) -> list[dict[str, Any]]:
    """Run regression with multiple seeds and collect coverage data."""
    params = CacheParams(sets=2, ways=2, line_bytes=16)
    data = []

    covered_bins: set[str] = set()
    covered_extended: set[str] = set()

    for seed in range(1, num_seeds + 1):
        result = run_core_regression(
            params=params,
            seeds=[seed],
            count=count_per_seed,
            report_dir=None,
        )

        coverage = result["coverage"]
        current_bins = coverage.get("bins", {})
        current_extended_bins = coverage.get("extended_bins", {})

        covered_bins.update(k for k, v in current_bins.items() if v > 0)
        covered_extended.update(k for k, v in current_extended_bins.items() if v > 0)

        data.append({
            "seed": seed,
            "coverage_percent": coverage["coverage_percent"],
            "covered_bins": len(covered_bins),
            "total_bins": coverage["total_bins"],
            "extended_coverage_percent": coverage["extended_coverage_percent"],
            "extended_covered": len(covered_extended),
            "extended_total": coverage["extended_total"],
            "cumulative_covered": sorted(list(covered_bins)),
            "cumulative_extended_covered": sorted(list(covered_extended)),
        })

    return data


def generate_ascii_chart(data: list[dict[str, Any]]) -> str:
    """Generate ASCII bar chart showing coverage progression."""
    max_width = 60

    lines = [
        "",
        "Coverage Convergence by Seed",
        "=" * 80,
        "",
        f"{'Seed':<6} {'Core Cov':<12} {'Ext Cov':<12} {'Cumulative':<40}",
        "-" * 80,
    ]

    for entry in data:
        core_bar = "█" * int(entry["coverage_percent"] / 100 * max_width)
        ext_bar = "░" * int(entry["extended_coverage_percent"] / 100 * max_width)

        combined_bar = ""
        for i in range(max_width):
            if i < len(core_bar):
                combined_bar += "█"
            elif i < len(core_bar) + len(ext_bar):
                combined_bar += "░"
            else:
                combined_bar += " "

        lines.append(
            f"{entry['seed']:<6} "
            f"{entry['coverage_percent']:6.1f}% ({entry['covered_bins']}/{entry['total_bins']}) "
            f"{entry['extended_coverage_percent']:6.1f}% ({entry['extended_covered']}/{entry['extended_total']}) "
            f"|{combined_bar}|"
        )

    lines.append("")
    lines.append("Legend: █ = Required coverage, ░ = Extended coverage")
    lines.append("")

    return "\n".join(lines)


def write_csv(data: list[dict[str, Any]], output_path: str | Path) -> None:
    """Write convergence data to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "seed",
            "coverage_percent",
            "covered_bins",
            "total_bins",
            "extended_coverage_percent",
            "extended_covered",
            "extended_total",
        ])
        for entry in data:
            writer.writerow([
                entry["seed"],
                entry["coverage_percent"],
                entry["covered_bins"],
                entry["total_bins"],
                entry["extended_coverage_percent"],
                entry["extended_covered"],
                entry["extended_total"],
            ])


def write_report(data: list[dict[str, Any]], output_path: str | Path) -> None:
    """Write convergence report in Markdown format."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    last_entry = data[-1]

    lines = [
        "# Coverage Convergence Analysis Report",
        "",
        f"Generated: {__import__('datetime').datetime.now().isoformat()}",
        "",
        "## Executive Summary",
        "",
        f"- Total seeds: {len(data)}",
        f"- Transactions per seed: 500",
        f"- Final core coverage: {last_entry['coverage_percent']:.1f}% ({last_entry['covered_bins']}/{last_entry['total_bins']})",
        f"- Final extended coverage: {last_entry['extended_coverage_percent']:.1f}% ({last_entry['extended_covered']}/{last_entry['extended_total']})",
        "",
        "## Convergence Trend",
        "",
        "### ASCII Chart",
        "",
        "```",
        generate_ascii_chart(data),
        "```",
        "",
        "### Detailed Table",
        "",
        "| Seed | Core Coverage | Extended Coverage | Cumulative Bins |",
        "| --- | --- | --- | --- |",
    ]

    for entry in data:
        lines.append(
            f"| {entry['seed']} | {entry['coverage_percent']:.1f}% ({entry['covered_bins']}/{entry['total_bins']}) | "
            f"{entry['extended_coverage_percent']:.1f}% ({entry['extended_covered']}/{entry['extended_total']}) | "
            f"{entry['covered_bins']} |"
        )

    lines.append("")
    lines.append("## Convergence Analysis")
    lines.append("")
    lines.append("### Rate of Coverage Growth")
    lines.append("")

    for i in range(1, len(data)):
        prev = data[i - 1]
        curr = data[i]
        core_gain = curr["coverage_percent"] - prev["coverage_percent"]
        ext_gain = curr["extended_coverage_percent"] - prev["extended_coverage_percent"]
        lines.append(f"- Seed {i} → {i+1}: Core +{core_gain:.1f}%, Extended +{ext_gain:.1f}%")

    lines.append("")
    lines.append("### Saturation Point")
    lines.append("")

    stable_count = 0
    for i in range(3, len(data)):
        if abs(data[i]["coverage_percent"] - data[i - 1]["coverage_percent"]) < 1.0:
            stable_count += 1

    if stable_count >= len(data) - 3:
        lines.append("Coverage appears to be approaching saturation.")
    else:
        lines.append("Coverage is still growing; more seeds may yield additional coverage.")

    lines.append("")
    lines.append("## Uncovered Bins Analysis")
    lines.append("")

    all_required = set()
    all_extended = set()
    for entry in data:
        for bin_name in entry.get("cumulative_covered", []):
            if not bin_name.startswith("cross.") and not bin_name.startswith("policy."):
                all_required.add(bin_name)
        for bin_name in entry.get("cumulative_extended_covered", []):
            all_extended.add(bin_name)

    lines.append(f"- Covered required bins: {len(all_required)}")
    lines.append(f"- Covered extended bins: {len(all_extended)}")
    lines.append("")

    path.write_text("\n".join(lines))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate coverage convergence chart")
    parser.add_argument("--seeds", type=int, default=10, help="Number of seeds to run")
    parser.add_argument("--count", type=int, default=500, help="Transactions per seed")
    parser.add_argument(
        "--output",
        default="reports/coverage_convergence.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--report",
        default="reports/coverage_convergence.md",
        help="Output report path",
    )
    args = parser.parse_args()

    print(f"Running {args.seeds} seeds with {args.count} transactions each...")

    data = generate_convergence_data(args.seeds, args.count)

    write_csv(data, args.output)
    write_report(data, args.report)

    print(f"\nGenerated convergence data: {args.output}")
    print(f"Generated convergence report: {args.report}")

    last = data[-1]
    print(f"\nFinal coverage:")
    print(f"  Core: {last['coverage_percent']:.1f}% ({last['covered_bins']}/{last['total_bins']})")
    print(f"  Extended: {last['extended_coverage_percent']:.1f}% ({last['extended_covered']}/{last['extended_total']})")


if __name__ == "__main__":
    main()
