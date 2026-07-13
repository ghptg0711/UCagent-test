#!/usr/bin/env python3
"""Generate an SVG coverage-convergence chart from a CSV report."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from xml.sax.saxutils import escape

WIDTH = 800
HEIGHT = 400
MARGIN = 60
ANNOTATIONS = {
    2: "Round 2: constraint inventory",
    4: "Round 4: parameterized strategy",
    7: "Round 7: review findings",
    9: "Rounds 8-9: real DUT and RTL fix",
    11: "P1.3: same-set constraint",
}


def _read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"iteration", "coverage_percent", "tests_passed"}
        missing = required.difference(reader.fieldnames or ())
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"missing required CSV columns: {names}")
        rows = list(reader)
    if not rows:
        raise ValueError("coverage CSV contains no data rows")
    return rows


def generate_trend_svg(csv_path: str | Path, output_path: str | Path) -> None:
    """Write an SVG chart showing coverage convergence over iterations."""
    rows = _read_rows(Path(csv_path))
    iterations = [int(row["iteration"]) for row in rows]
    coverage = [float(row["coverage_percent"]) for row in rows]
    tests = [int(row["tests_passed"]) for row in rows]
    if any(value < 0 or value > 100 for value in coverage):
        raise ValueError("coverage_percent values must be between 0 and 100")

    plot_width = WIDTH - 2 * MARGIN
    plot_height = HEIGHT - 2 * MARGIN
    max_tests = max(max(tests), 1)
    denominator = max(len(iterations) - 1, 1)

    def x_scale(index: int) -> float:
        return MARGIN + (index / denominator) * plot_width

    def y_coverage(value: float) -> float:
        return HEIGHT - MARGIN - (value / 100.0) * plot_height

    def y_tests(value: int) -> float:
        return HEIGHT - MARGIN - (value / max_tests) * plot_height * 0.8

    svg = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
            f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">'
        ),
        "<style>",
        "  .axis { stroke: #333; stroke-width: 1.5; fill: none; }",
        "  .grid { stroke: #ddd; stroke-width: 0.5; fill: none; stroke-dasharray: 4,4; }",
        "  .label { font-family: sans-serif; font-size: 11px; fill: #333; }",
        "  .title { font-family: sans-serif; font-size: 14px; font-weight: bold; fill: #333; }",
        "  .legend { font-family: sans-serif; font-size: 11px; fill: #333; }",
        "</style>",
        f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="white"/>',
        (
            f'<text x="{WIDTH / 2}" y="20" text-anchor="middle" '
            'class="title">Coverage Convergence Trend</text>'
        ),
    ]

    for percent in (0, 25, 50, 75, 100):
        y = y_coverage(percent)
        svg.append(f'<line x1="{MARGIN}" y1="{y}" x2="{WIDTH - MARGIN}" y2="{y}" class="grid"/>')
        svg.append(
            f'<text x="{MARGIN - 5}" y="{y + 4}" text-anchor="end" class="label">{percent}%</text>'
        )

    for index, iteration in enumerate(iterations):
        svg.append(
            f'<text x="{x_scale(index)}" y="{HEIGHT - MARGIN + 18}" '
            f'text-anchor="middle" class="label">Iter {iteration}</text>'
        )

    svg.extend(
        [
            f'<line x1="{MARGIN}" y1="{MARGIN}" x2="{MARGIN}" '
            f'y2="{HEIGHT - MARGIN}" class="axis"/>',
            f'<line x1="{MARGIN}" y1="{HEIGHT - MARGIN}" x2="{WIDTH - MARGIN}" '
            f'y2="{HEIGHT - MARGIN}" class="axis"/>',
        ]
    )
    coverage_points = " ".join(
        f"{x_scale(index)},{y_coverage(value)}" for index, value in enumerate(coverage)
    )
    svg.append(
        f'<polyline points="{coverage_points}" fill="none" stroke="#2563eb" stroke-width="2.5"/>'
    )
    for index, value in enumerate(coverage):
        svg.append(f'<circle cx="{x_scale(index)}" cy="{y_coverage(value)}" r="4" fill="#2563eb"/>')

    test_points = " ".join(
        f"{x_scale(index)},{y_tests(value)}" for index, value in enumerate(tests)
    )
    svg.extend(
        [
            f'<polyline points="{test_points}" fill="none" stroke="#16a34a" '
            'stroke-width="2" stroke-dasharray="5,3"/>',
            f'<rect x="{WIDTH - 180}" y="35" width="170" height="55" '
            'fill="white" stroke="#ccc" rx="4"/>',
            f'<line x1="{WIDTH - 170}" y1="50" x2="{WIDTH - 140}" y2="50" '
            'stroke="#2563eb" stroke-width="2.5"/>',
            f'<text x="{WIDTH - 135}" y="54" class="legend">Coverage %</text>',
            f'<line x1="{WIDTH - 170}" y1="70" x2="{WIDTH - 140}" y2="70" '
            'stroke="#16a34a" stroke-width="2" stroke-dasharray="5,3"/>',
            f'<text x="{WIDTH - 135}" y="74" class="legend">Tests Passed</text>',
        ]
    )

    final_x = x_scale(len(iterations) - 1) + 10
    svg.append(
        f'<text x="{final_x}" y="{y_coverage(coverage[-1])}" class="label" '
        f'fill="#2563eb" font-weight="bold">{coverage[-1]:.1f}%</text>'
    )
    for iteration, label in ANNOTATIONS.items():
        if iteration not in iterations:
            continue
        index = iterations.index(iteration)
        x = x_scale(index)
        y = y_coverage(coverage[index])
        svg.append(
            f'<polygon points="{x},{y - 6} {x + 5},{y} {x},{y + 6} {x - 5},{y}" fill="#dc2626"/>'
        )
        text_y = y - 12 if y > MARGIN + 30 else y + 20
        svg.append(
            f'<text x="{x}" y="{text_y}" text-anchor="middle" class="label" '
            f'fill="#dc2626" font-size="9px">{escape(label)}</text>'
        )

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join([*svg, "</svg>"]) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", nargs="?", default="reports/coverage_convergence.csv")
    parser.add_argument("output_path", nargs="?", default="reports/coverage_convergence_trend.svg")
    args = parser.parse_args()
    generate_trend_svg(args.csv_path, args.output_path)
    print(f"Coverage trend chart saved to: {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
