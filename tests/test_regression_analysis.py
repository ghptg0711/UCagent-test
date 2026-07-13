import json

from cache_vip.regression import run_core_regression, run_enhanced_regression
from cache_vip.regression_analysis import format_markdown, write_reports


def test_write_core_reports(tmp_path) -> None:
    summary = run_core_regression(seeds=(1,), count=10)

    write_reports(tmp_path, summary)

    saved = json.loads((tmp_path / "core_regression_summary.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "core_regression_summary.md").read_text(encoding="utf-8")
    assert saved["status"] == "PASS"
    assert "## Coverage" in markdown
    assert "## Fault Detection" in markdown


def test_format_enhanced_report_includes_dut_and_fault_sections() -> None:
    summary = run_enhanced_regression(core_seeds=(1,), dut_seeds=(2,), core_count=10, dut_count=10)

    markdown = format_markdown(summary)

    assert "## Coverage Summary" in markdown
    assert "## Core Regression" in markdown
    assert "## DUT Regression" in markdown
    assert "## Fault Detection" in markdown
