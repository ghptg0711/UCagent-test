from __future__ import annotations

from pathlib import Path

import pytest

from cache_vip.reference_model import CacheParams
from scripts.generate_coverage_trend import generate_trend_svg
from scripts.run_large_scale_regression import _is_same_set_revisit


def test_generate_single_point_chart(tmp_path: Path) -> None:
    source = tmp_path / "coverage.csv"
    destination = tmp_path / "chart.svg"
    source.write_text(
        "iteration,coverage_percent,tests_passed,bugs_found\n1,75.5,0,0\n",
        encoding="utf-8",
    )

    generate_trend_svg(source, destination)

    svg = destination.read_text(encoding="utf-8")
    assert svg.startswith("<svg")
    assert "75.5%" in svg
    assert svg.endswith("</svg>\n")


def test_rejects_missing_columns(tmp_path: Path) -> None:
    source = tmp_path / "coverage.csv"
    source.write_text("iteration,coverage_percent\n1,50\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required CSV columns"):
        generate_trend_svg(source, tmp_path / "chart.svg")


def test_rejects_out_of_range_coverage(tmp_path: Path) -> None:
    source = tmp_path / "coverage.csv"
    source.write_text(
        "iteration,coverage_percent,tests_passed\n1,101,1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="between 0 and 100"):
        generate_trend_svg(source, tmp_path / "chart.svg")


def test_large_scale_regression_detects_real_same_set_revisits() -> None:
    params = CacheParams(sets=4, line_bytes=64)
    visited_sets: set[int] = set()

    assert _is_same_set_revisit(0x00, params, visited_sets) is False
    assert _is_same_set_revisit(0x40, params, visited_sets) is False
    assert _is_same_set_revisit(0x100, params, visited_sets) is True
