from cache_vip.regression import run_core_regression


def test_core_regression_summary_passes_and_detects_faults():
    summary = run_core_regression(seeds=(1,), count=20)

    assert summary["status"] == "PASS"
    assert summary["coverage"]["coverage_percent"] == 100.0
    assert summary["coverage"]["bins"]["replacement.dirty"] > 0
    assert all(summary["fault_detection"].values())
    assert summary["directed"]["status"] == "PASS"
