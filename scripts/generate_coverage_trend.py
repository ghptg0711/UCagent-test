#!/usr/bin/env python3
"""Generate coverage convergence trend chart from CSV data."""
import csv
import sys
from pathlib import Path

def generate_trend_svg(csv_path: str, output_path: str):
    """Generate an SVG chart showing coverage convergence over iterations."""
    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    iterations = [int(r['iteration']) for r in rows]
    coverage = [float(r['coverage_percent']) for r in rows]
    tests = [int(r['tests_passed']) for r in rows]
    bugs = [int(r['bugs_found']) for r in rows]

    # SVG dimensions
    width = 800
    height = 400
    margin = 60
    plot_w = width - 2 * margin
    plot_h = height - 2 * margin

    # Scales
    max_cov = 100.0
    max_tests = max(tests)
    max_bugs = max(bugs) if bugs else 1

    def x_scale(i):
        return margin + (i / (len(iterations) - 1)) * plot_w

    def y_cov(v):
        return height - margin - (v / max_cov) * plot_h

    def y_tests(v):
        return height - margin - (v / max_tests) * plot_h * 0.8

    # Build SVG
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>',
        '  .axis { stroke: #333; stroke-width: 1.5; fill: none; }',
        '  .grid { stroke: #ddd; stroke-width: 0.5; fill: none; stroke-dasharray: 4,4; }',
        '  .label { font-family: sans-serif; font-size: 11px; fill: #333; }',
        '  .title { font-family: sans-serif; font-size: 14px; font-weight: bold; fill: #333; }',
        '  .legend { font-family: sans-serif; font-size: 11px; fill: #333; }',
        '</style>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
        f'<text x="{width/2}" y="20" text-anchor="middle" class="title">Coverage Convergence Trend</text>',
    ]

    # Grid lines
    for pct in [0, 25, 50, 75, 100]:
        y = y_cov(pct)
        svg_parts.append(f'<line x1="{margin}" y1="{y}" x2="{width-margin}" y2="{y}" class="grid"/>')
        svg_parts.append(f'<text x="{margin-5}" y="{y+4}" text-anchor="end" class="label">{pct}%</text>')

    # X axis labels
    for i, it in enumerate(iterations):
        x = x_scale(i)
        svg_parts.append(f'<text x="{x}" y="{height-margin+18}" text-anchor="middle" class="label">Iter {it}</text>')

    # Axes
    svg_parts.append(f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height-margin}" class="axis"/>')
    svg_parts.append(f'<line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" class="axis"/>')

    # Coverage line (blue)
    points = ' '.join(f'{x_scale(i)},{y_cov(c)}' for i, c in enumerate(coverage))
    svg_parts.append(f'<polyline points="{points}" fill="none" stroke="#2563eb" stroke-width="2.5"/>')
    for i, c in enumerate(coverage):
        svg_parts.append(f'<circle cx="{x_scale(i)}" cy="{y_cov(c)}" r="4" fill="#2563eb"/>')

    # Tests line (green)
    points_t = ' '.join(f'{x_scale(i)},{y_tests(t)}' for i, t in enumerate(tests))
    svg_parts.append(f'<polyline points="{points_t}" fill="none" stroke="#16a34a" stroke-width="2" stroke-dasharray="5,3"/>')

    # Legend
    svg_parts.append(f'<rect x="{width-180}" y="35" width="170" height="55" fill="white" stroke="#ccc" rx="4"/>')
    svg_parts.append(f'<line x1="{width-170}" y1="50" x2="{width-140}" y2="50" stroke="#2563eb" stroke-width="2.5"/>')
    svg_parts.append(f'<text x="{width-135}" y="54" class="legend">Coverage %</text>')
    svg_parts.append(f'<line x1="{width-170}" y1="70" x2="{width-140}" y2="70" stroke="#16a34a" stroke-width="2" stroke-dasharray="5,3"/>')
    svg_parts.append(f'<text x="{width-135}" y="74" class="legend">Tests Passed</text>')

    # Final values annotation
    svg_parts.append(f'<text x="{x_scale(len(iterations)-1)+10}" y="{y_cov(coverage[-1])}" class="label" fill="#2563eb" font-weight="bold">{coverage[-1]:.1f}%</text>')

    svg_parts.append('</svg>')

    with open(output_path, 'w') as f:
        f.write('\n'.join(svg_parts))
    print(f"Coverage trend chart saved to: {output_path}")


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "reports/coverage_convergence.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "reports/coverage_convergence_trend.svg"
    generate_trend_svg(csv_path, output_path)
