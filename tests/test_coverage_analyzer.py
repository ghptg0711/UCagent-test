import json

from cache_vip.coverage_analyzer import CoverageHoleAnalyzer, HoleCategory


def test_coverage_hole_analyzer_classifies_all_supported_bin_families(tmp_path) -> None:
    missing = [
        "op.read",
        "size.4",
        "access.write_miss",
        "access.read_hit",
        "access.read_miss",
        "replacement.dirty",
        "replacement.clean",
        "replacement.unknown",
        "mask.full",
        "mask.single",
        "mask.sparse",
        "mask.unknown",
        "addr.same_set",
        "addr.line_boundary",
        "addr.back_to_back_same_line",
        "addr.stride_access_pattern",
        "addr.unknown",
        "latency.long",
        "latency.short",
        "latency.unknown",
        "cross.size_mask.size4_sparse",
        "cross.replacement_type.read_dirty",
        "cross.access_latency.read_miss_long",
        "cross.unknown.value",
        "policy.write_allocate.enabled",
        "policy.replacement.fifo_eviction",
        "policy.unknown.value",
        "custom.unclassified",
    ]
    analyzer = CoverageHoleAnalyzer(
        {"missing": missing[:14], "extended_missing": missing[14:]}
    )

    attributions = analyzer.analyze()

    assert len(attributions) == len(missing)
    assert {item.category for item in attributions} == {
        HoleCategory.HARD_TO_REACH,
        HoleCategory.CONFIG_BLOCKED,
        HoleCategory.POTENTIALLY_REACHABLE,
    }
    assert any(item.associated_bugs == ["BUG-011"] for item in attributions)

    report = tmp_path / "coverage_holes.md"
    analyzer.write_report(report)
    report_text = report.read_text(encoding="utf-8")
    assert "Coverage Hole Attribution Report" in report_text
    assert "BUG-011" in report_text

    payload = json.loads(analyzer.to_json())
    assert payload["total_missing"] == len(missing)
    assert sum(payload["by_category"].values()) == len(missing)


def test_coverage_hole_analyzer_resets_previous_results() -> None:
    analyzer = CoverageHoleAnalyzer({"missing": ["op.write"]})
    assert len(analyzer.analyze()) == 1

    analyzer.summary = {"missing": []}

    assert analyzer.analyze() == []
