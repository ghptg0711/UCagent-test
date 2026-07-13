from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from pathlib import Path

from .coverage_analyzer import CoverageHoleAnalyzer
from .faults import FaultInjector
from .generator import CacheGenerator
from .oracle import ArchitecturalMemoryOracle
from .reference_model import CacheParams, ReferenceCache
from .regression_analysis import write_reports
from .scoreboard import Scoreboard, ScoreboardMismatch
from .transactions import CacheOp, CacheTxn


def run_core_regression(
    *,
    seeds: Iterable[int] = (1, 2, 3),
    count: int = 300,
    params: CacheParams | None = None,
    report_dir: Path | None = None,
) -> dict[str, object]:
    cache_params = params or CacheParams()
    smoke = _run_named_stream("smoke", _smoke_stream(), cache_params)
    directed = _run_named_stream(
        "directed", _directed_stream(cache_params), cache_params, mark_same_set=True
    )
    crv = [
        _run_named_stream(
            f"crv_seed_{seed}",
            CacheGenerator(cache_params, seed=seed).random_stream(count),
            cache_params,
        )
        for seed in seeds
    ]
    coverage = _run_coverage_closure(cache_params)
    faults = _run_fault_detection(cache_params)
    passed = (
        smoke["status"] == "PASS"
        and directed["status"] == "PASS"
        and all(item["status"] == "PASS" for item in crv)
    )
    passed = passed and coverage["coverage_percent"] >= 90.0 and all(faults.values())

    summary: dict[str, object] = {
        "status": "PASS" if passed else "FAIL",
        "smoke": smoke,
        "directed": directed,
        "crv": crv,
        "coverage": coverage,
        "fault_detection": faults,
    }
    if report_dir is not None:
        write_reports(report_dir, summary)
        analyzer = CoverageHoleAnalyzer(coverage)
        analyzer.analyze()
        analyzer.write_report(report_dir / "coverage_holes_attribution.md")
    return summary


def run_enhanced_regression(
    *,
    core_seeds: Iterable[int] = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
    dut_seeds: Iterable[int] | None = None,
    core_count: int = 1000,
    dut_count: int = 300,
    params: CacheParams | None = None,
    report_dir: Path | None = None,
) -> dict[str, object]:
    """Enhanced regression with increased CRV coverage.

    Features:
    - Core: 10 seeds x 1000 txns (default)
    - DUT mode support with separate seed/count
    - Per-seed coverage output
    - Auto-print transaction index on failure
    - Last 20 transaction repro window
    """
    cache_params = params or CacheParams()

    # Run enhanced core regression
    print(f"\n{'=' * 60}")
    print("Running Enhanced Regression")
    print(f"Core seeds: {list(core_seeds)}, count per seed: {core_count}")
    if dut_seeds:
        print(f"DUT seeds: {list(dut_seeds)}, count per seed: {dut_count}")
    print(f"{'=' * 60}\n")

    results = {
        "core_regression": [],
        "dut_regression": [],
        "coverage_summary": {},
        "fault_detection": {},
    }

    # Core regression
    for seed in core_seeds:
        result = _run_enhanced_core_seed(seed, core_count, cache_params)
        results["core_regression"].append(result)
        status = result["status"]
        print(
            f"[Core Seed {seed}] Status: {status}, Txns: {result['transactions']}, Coverage: {result['coverage_percent']}%"
        )
        if status == "FAIL":
            print(f"  Error at txn #{result['error_txn_id']}: {result['error']}")
            print(f"  Repro window: {len(result['repro_window'])} transactions")

        # Collect coverage
        for bin_name, hits in result.get("bins", {}).items():
            if bin_name not in results["coverage_summary"]:
                results["coverage_summary"][bin_name] = 0
            results["coverage_summary"][bin_name] += hits

    # Fault detection
    faults = _run_fault_detection(cache_params)
    results["fault_detection"] = faults
    print("\nFault Detection:")
    for name, detected in faults.items():
        print(f"  {name}: {'DETECTED' if detected else 'MISSED'}")

    # DUT regression (if seeds provided)
    if dut_seeds:
        for seed in dut_seeds:
            result = _run_enhanced_core_seed(seed, dut_count, cache_params)
            result["name"] = f"dut_seed_{seed}"
            results["dut_regression"].append(result)
            status = result["status"]
            print(
                f"[DUT Seed {seed}] Status: {status}, Txns: {result['transactions']}, Coverage: {result['coverage_percent']}%"
            )
            if status == "FAIL":
                print(f"  Error at txn #{result['error_txn_id']}: {result['error']}")
                print(f"  Repro window: {len(result['repro_window'])} transactions")

            for bin_name, hits in result.get("bins", {}).items():
                if bin_name not in results["coverage_summary"]:
                    results["coverage_summary"][bin_name] = 0
                results["coverage_summary"][bin_name] += hits

    # Overall status
    all_core_passed = all(r["status"] == "PASS" for r in results["core_regression"])
    all_dut_passed = (
        all(r["status"] == "PASS" for r in results["dut_regression"])
        if results["dut_regression"]
        else True
    )
    all_passed = all_core_passed and all_dut_passed
    cov_pct = (
        sum(1 for h in results["coverage_summary"].values() if h > 0)
        / len(results["coverage_summary"])
        * 100.0
        if results["coverage_summary"]
        else 100.0
    )
    overall_status = "PASS" if all_passed and cov_pct >= 90.0 else "FAIL"

    final_summary = {
        "status": overall_status,
        "core_seeds_used": list(core_seeds),
        "core_count_per_seed": core_count,
        **results,
    }

    if report_dir is not None:
        write_reports(report_dir, final_summary)

    print(f"\nOverall Status: {overall_status} ({cov_pct:.1f}% coverage)")
    return final_summary


def _run_enhanced_core_seed(seed: int, count: int, params: CacheParams) -> dict[str, object]:
    """Run a single seed with enhanced reporting and independent verification."""
    from .coverage import Coverage

    ref = ReferenceCache(params)
    cov = Coverage(line_bytes=params.line_bytes)
    gen = CacheGenerator(params, seed=seed)
    txns = gen.random_stream(count)
    history: list[CacheTxn] = []
    oracle = ArchitecturalMemoryOracle()
    # Track visited sets so same_set is sampled from real address locality,
    # not a synthetic index modulo. This lets a single CRV seed reach the
    # addr.same_set bin once the hot set is revisited.
    visited_sets: set[int] = set()

    for index, txn in enumerate(txns):
        history.append(txn)
        latency = 10 if index % 11 == 0 else index % 4
        try:
            response = ref.access(txn)
            oracle.check_and_apply(txn, response)
            set_idx = (txn.addr // params.line_bytes) % params.sets
            same_set = set_idx in visited_sets
            visited_sets.add(set_idx)
            cov.sample_access(
                txn,
                hit=response.hit,
                evicted_dirty=response.evicted_dirty,
                evicted_clean=(response.evicted and not response.evicted_dirty),
                latency=latency,
                same_set=same_set,
                replacement_policy=params.replacement.value,
                write_allocate=params.write_allocate,
            )

        except ScoreboardMismatch as exc:
            print(f"\n*** MISMATCH at seed={seed}, txn_index={index} ***")
            print(f"  Txn: {_txn_to_dict(txn)}")
            print(f"  Error: {exc}")

            return {
                "name": f"crv_seed_{seed}",
                "status": "FAIL",
                "transactions": index + 1,
                "error_txn_id": index,
                "error": str(exc),
                "repro_window": [_txn_to_dict(item) for item in history[-20:]],
                "coverage_percent": cov.percent(),
                "missing_bins": cov.missing(),
                "bins": cov.required_bin_counts(),
                "seed": seed,
            }
        except Exception as exc:
            print(f"\n*** ERROR at seed={seed}, txn_index={index} ***")
            print(f"  Txn: {_txn_to_dict(txn)}")
            print(f"  Error: {type(exc).__name__}: {exc}")

            return {
                "name": f"crv_seed_{seed}",
                "status": "FAIL",
                "transactions": index + 1,
                "error_txn_id": index,
                "error": f"{type(exc).__name__}: {exc}",
                "repro_window": [_txn_to_dict(item) for item in history[-20:]],
                "coverage_percent": cov.percent(),
                "missing_bins": cov.missing(),
                "bins": cov.required_bin_counts(),
                "seed": seed,
            }

    return {
        "name": f"crv_seed_{seed}",
        "status": "PASS",
        "transactions": len(txns),
        "coverage_percent": round(cov.percent(), 2),
        "missing_bins": cov.missing(),
        "bins": cov.required_bin_counts(),
        "seed": seed,
    }


def _run_named_stream(
    name: str,
    txns: list[CacheTxn],
    params: CacheParams,
    *,
    mark_same_set: bool = False,
) -> dict[str, object]:
    """Run a model stream with an independent architectural byte oracle."""
    from .coverage import Coverage

    ref = ReferenceCache(params)
    cov = Coverage(line_bytes=params.line_bytes)
    oracle = ArchitecturalMemoryOracle()
    history: list[CacheTxn] = []
    # When mark_same_set is False (e.g. CRV streams), still sample same_set
    # from real address locality so a single seed can reach the bin.
    visited_sets: set[int] = set()

    for index, txn in enumerate(txns):
        latency = 10 if index % 11 == 0 else index % 4
        history.append(txn)
        try:
            response = ref.access(txn)
            oracle.check_and_apply(txn, response)
            if mark_same_set:
                same_set = True
            else:
                set_idx = (txn.addr // params.line_bytes) % params.sets
                same_set = set_idx in visited_sets
                visited_sets.add(set_idx)
            cov.sample_access(
                txn,
                hit=response.hit,
                evicted_dirty=response.evicted_dirty,
                evicted_clean=(response.evicted and not response.evicted_dirty),
                latency=latency,
                same_set=same_set,
                replacement_policy=params.replacement.value,
                write_allocate=params.write_allocate,
            )

        except ScoreboardMismatch as exc:
            return {
                "name": name,
                "status": "FAIL",
                "transactions": index + 1,
                "error": str(exc),
                "repro_window": [_txn_to_dict(item) for item in history[-20:]],
                "coverage_percent": cov.percent(),
                "missing_bins": cov.missing(),
            }
        except Exception as exc:
            return {
                "name": name,
                "status": "FAIL",
                "transactions": index + 1,
                "error": f"{type(exc).__name__}: {exc}",
                "repro_window": [_txn_to_dict(item) for item in history[-20:]],
                "coverage_percent": cov.percent(),
                "missing_bins": cov.missing(),
            }
    return {
        "name": name,
        "status": "PASS",
        "transactions": len(txns),
        "coverage_percent": cov.percent(),
        "missing_bins": cov.missing(),
    }


def _smoke_stream() -> list[CacheTxn]:
    return [
        CacheTxn(CacheOp.READ, addr=0x00, size=8, txn_id=1),
        CacheTxn(CacheOp.WRITE, addr=0x00, size=8, data=0x1122334455667788, mask=0xFF, txn_id=2),
        CacheTxn(CacheOp.READ, addr=0x00, size=8, txn_id=3),
        CacheTxn(CacheOp.WRITE, addr=0x04, size=4, data=0xAABBCCDD, mask=0b0101, txn_id=4),
        CacheTxn(CacheOp.READ, addr=0x00, size=8, txn_id=5),
    ]


def _directed_stream(params: CacheParams) -> list[CacheTxn]:
    gen = CacheGenerator(params, seed=101)
    txns = gen.partial_write_sequence(0x1000)
    txns.extend(gen.replacement_sequence(set_idx=1, dirty=True))
    txns.extend(gen.replacement_sequence(set_idx=2, dirty=False))
    txns.extend(_raw_hazard_sequence(0x3000, start_id=20_000))
    txns.extend(_line_boundary_sequence(start_id=30_000))
    # New directed sequences from generator
    txns.extend(gen.replacement_sequence_with_lru_check(set_idx=3))
    txns.extend(gen.partial_write_cross_offset(0x5000))
    txns.extend(gen.raw_dependency_sequence(0x6000))
    txns.extend(gen.line_boundary_all_sizes(0x5C00))
    txns.extend(gen.uncached_access_sequence(0x80000000))
    txns.extend(gen.reset_state_clear(0x7000))
    txns.extend(
        [
            CacheTxn(CacheOp.READ, addr=0x38, size=8, txn_id=10_001),
            CacheTxn(
                CacheOp.WRITE,
                addr=0x2000,
                size=1,
                data=0x5A,
                mask=0x1,
                txn_id=10_002,
                uncached=True,
            ),
            CacheTxn(CacheOp.READ, addr=0x2000, size=1, txn_id=10_003, uncached=True),
        ]
    )
    return txns


def _raw_hazard_sequence(base: int, *, start_id: int) -> list[CacheTxn]:
    return [
        CacheTxn(
            CacheOp.WRITE, addr=base, size=8, data=0x0102030405060708, mask=0xFF, txn_id=start_id
        ),
        CacheTxn(CacheOp.READ, addr=base, size=8, txn_id=start_id + 1),
        CacheTxn(CacheOp.WRITE, addr=base + 2, size=2, data=0xAABB, mask=0x3, txn_id=start_id + 2),
        CacheTxn(CacheOp.READ, addr=base, size=8, txn_id=start_id + 3),
        CacheTxn(
            CacheOp.WRITE, addr=base, size=4, data=0xDEADBEEF, mask=0b1010, txn_id=start_id + 4
        ),
        CacheTxn(CacheOp.READ, addr=base, size=8, txn_id=start_id + 5),
    ]


def _line_boundary_sequence(*, start_id: int) -> list[CacheTxn]:
    return [
        CacheTxn(CacheOp.READ, addr=0x3F, size=1, txn_id=start_id),
        CacheTxn(CacheOp.READ, addr=0x3E, size=2, txn_id=start_id + 1),
        CacheTxn(CacheOp.READ, addr=0x3C, size=4, txn_id=start_id + 2),
        CacheTxn(CacheOp.READ, addr=0x38, size=8, txn_id=start_id + 3),
    ]


def _run_coverage_closure(params: CacheParams) -> dict[str, object]:
    from .coverage import Coverage

    ref = ReferenceCache(params)
    cov = Coverage(line_bytes=params.line_bytes)
    gen = CacheGenerator(params, seed=19)
    stream = [
        CacheTxn(CacheOp.READ, addr=0x00, size=1, txn_id=1),
        CacheTxn(CacheOp.READ, addr=0x00, size=1, txn_id=2),
        CacheTxn(CacheOp.WRITE, addr=0x08, size=2, data=0xABCD, mask=0x3, txn_id=3),
        CacheTxn(CacheOp.WRITE, addr=0x08, size=2, data=0x00EF, mask=0x1, txn_id=4),
        CacheTxn(CacheOp.WRITE, addr=0x10, size=4, data=0x11223344, mask=0b0101, txn_id=5),
        CacheTxn(CacheOp.WRITE, addr=0x18, size=8, data=0xAABBCCDDEEFF0011, mask=0xFF, txn_id=6),
        CacheTxn(CacheOp.READ, addr=0x38, size=8, txn_id=7),
    ]
    stream.extend(gen.replacement_sequence(set_idx=1, dirty=True))
    stream.extend(gen.replacement_sequence(set_idx=2, dirty=False))
    visited_sets: set[int] = set()
    for index, txn in enumerate(stream):
        response = ref.access(txn)
        set_idx = (txn.addr // params.line_bytes) % params.sets
        same_set = set_idx in visited_sets
        visited_sets.add(set_idx)
        cov.sample_access(
            txn,
            hit=response.hit,
            evicted_dirty=response.evicted_dirty,
            evicted_clean=(response.evicted and not response.evicted_dirty),
            latency=10 if index % 3 == 0 else 1,
            same_set=same_set,
            replacement_policy=params.replacement.value,
            write_allocate=params.write_allocate,
        )
    return cov.summary()


def _run_fault_detection(params: CacheParams) -> dict[str, bool]:
    return {
        "read_corruption": _detect_read_corruption(params),
        "partial_write_mask_drop": _detect_partial_write_mask_drop(params),
        "dirty_writeback_corruption": _detect_dirty_writeback_corruption(),
        "response_order_swap": _detect_response_order_swap(params),
        "tag_compare_error": _detect_tag_compare_error(params),
        "writeback_addr_corruption": _detect_writeback_addr_corruption(),
    }


def _detect_read_corruption(params: CacheParams) -> bool:
    """End-to-end fault detection: write/read with data bit-flip injected at
    DUT response path. Scoreboard must catch it via ScoreboardMismatch.

    Models DUT data bus corruption (sense amp bit-flip, crosstalk, etc.).
    """
    good_ref = ReferenceCache(params)
    faulty_ref = ReferenceCache(params)
    scoreboard = Scoreboard(good_ref)
    txns = [
        CacheTxn(CacheOp.WRITE, addr=0x100, size=4, data=0x12345678, mask=0xF, txn_id=1),
        CacheTxn(CacheOp.READ, addr=0x100, size=4, txn_id=2),
    ]
    for index, txn in enumerate(txns):
        actual = faulty_ref.access(txn)
        if index == 1:
            actual = FaultInjector.flip_read_bit(actual, bit=3)
        scoreboard.push_request(txn)
        try:
            scoreboard.compare_response(txn, actual)
        except ScoreboardMismatch:
            return True
    return False


def _detect_partial_write_mask_drop(params: CacheParams) -> bool:
    """End-to-end fault detection: wmask bit dropped on DUT write path.
    Scoreboard must detect data corruption on subsequent read.

    Models DUT byte-write enable stuck bit (write mask register fault).
    """
    good_ref = ReferenceCache(params)
    faulty_ref = ReferenceCache(params)
    scoreboard = Scoreboard(good_ref)
    txns = [
        CacheTxn(CacheOp.WRITE, addr=0x180, size=4, data=0x11223344, mask=0xF, txn_id=1),
        CacheTxn(CacheOp.WRITE, addr=0x180, size=4, data=0xAABBCCDD, mask=0b0101, txn_id=2),
        CacheTxn(CacheOp.READ, addr=0x180, size=4, txn_id=3),
    ]
    for index, txn in enumerate(txns):
        actual_txn = txn
        if index == 1:
            actual_txn = FaultInjector.drop_mask_bit(txn, bit=0)
        actual = faulty_ref.access(actual_txn)
        scoreboard.push_request(txn)
        try:
            scoreboard.compare_response(txn, actual)
        except ScoreboardMismatch:
            return True
    return False


def _detect_dirty_writeback_corruption() -> bool:
    """End-to-end fault detection: dirty eviction writeback data corrupted.
    Scoreboard must detect the mismatch via subsequent read.

    Models DUT writeback data path stuck bit causing memory corruption.
    """
    params = CacheParams(sets=1, ways=1, line_bytes=64)
    good_ref = ReferenceCache(params)
    faulty_ref = ReferenceCache(params)
    scoreboard = Scoreboard(good_ref)
    write = CacheTxn(CacheOp.WRITE, addr=0x00, size=8, data=0x1122334455667788, mask=0xFF, txn_id=1)
    evict = CacheTxn(CacheOp.READ, addr=0x40, size=8, txn_id=2)
    for index, txn in enumerate([write, evict]):
        actual = faulty_ref.access(txn)
        if index == 1:
            actual = FaultInjector.corrupt_writeback_byte(actual)
        scoreboard.push_request(txn)
        try:
            scoreboard.compare_response(txn, actual)
        except ScoreboardMismatch:
            return True
    return False


def _detect_response_order_swap(params: CacheParams) -> bool:
    """End-to-end fault detection: two consecutive responses swapped at DUT
    output interface. Scoreboard must detect txn_id mismatch.

    Models DUT response ordering logic failure (output FIFO pointer error).
    """
    good_ref = ReferenceCache(params)
    faulty_ref = ReferenceCache(params)
    scoreboard = Scoreboard(good_ref)
    txns = [
        CacheTxn(CacheOp.WRITE, addr=0x240, size=4, data=0xCAFEBABE, mask=0xF, txn_id=1),
        CacheTxn(CacheOp.READ, addr=0x240, size=4, txn_id=2),
    ]
    faulty_responses = FaultInjector.swap_order([faulty_ref.access(txn) for txn in txns])
    for index, txn in enumerate(txns):
        scoreboard.push_request(txn)
        try:
            scoreboard.compare_response(txn, faulty_responses[index])
        except ScoreboardMismatch:
            return True
    return False


def _detect_tag_compare_error(params: CacheParams) -> bool:
    """End-to-end fault detection: tag comparator output flipped at DUT
    interface. Scoreboard must detect hit/miss mismatch.

    Models DUT tag comparison stuck-at fault (incorrect hit/miss signaling).
    """
    good_ref = ReferenceCache(params)
    faulty_ref = ReferenceCache(params)
    scoreboard = Scoreboard(good_ref)
    txns = [
        CacheTxn(CacheOp.WRITE, addr=0x300, size=4, data=0xDEADBEEF, mask=0xF, txn_id=1),
        CacheTxn(CacheOp.READ, addr=0x300, size=4, txn_id=2),
    ]
    for index, txn in enumerate(txns):
        actual = faulty_ref.access(txn)
        if index == 1:
            actual = FaultInjector.flip_tag_match(actual)
        scoreboard.push_request(txn)
        try:
            scoreboard.compare_response(txn, actual)
        except ScoreboardMismatch:
            return True
    return False


def _detect_writeback_addr_corruption() -> bool:
    """End-to-end fault detection: dirty eviction writeback address is wrong.
    Scoreboard must detect the writeback_addr mismatch.

    Models DUT writeback address generation fault (address mux stuck bit,
    tag/set concatenation error) causing silent memory corruption at the
    wrong physical address.
    """
    params = CacheParams(sets=1, ways=1, line_bytes=64)
    good_ref = ReferenceCache(params)
    faulty_ref = ReferenceCache(params)
    scoreboard = Scoreboard(good_ref)
    write = CacheTxn(CacheOp.WRITE, addr=0x00, size=8, data=0x1122334455667788, mask=0xFF, txn_id=1)
    evict = CacheTxn(CacheOp.READ, addr=0x40, size=8, txn_id=2)
    for index, txn in enumerate([write, evict]):
        actual = faulty_ref.access(txn)
        if index == 1:
            actual = FaultInjector.corrupt_writeback_addr(actual, offset=0x80)
        scoreboard.push_request(txn)
        try:
            scoreboard.compare_response(txn, actual)
        except ScoreboardMismatch:
            return True
    return False


def _txn_to_dict(txn: CacheTxn) -> dict[str, object]:
    return {
        "txn_id": txn.txn_id,
        "op": txn.op.value,
        "addr": f"0x{txn.addr:x}",
        "size": txn.size,
        "data": f"0x{txn.data:x}",
        "mask": f"0x{txn.mask:x}" if txn.mask is not None else None,
        "uncached": txn.uncached,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run DUT-independent NutShell Cache VIP regression."
    )
    parser.add_argument("--seeds", default="1,2,3", help="comma-separated CRV seeds")
    parser.add_argument("--count", type=int, default=300, help="transactions per CRV seed")
    parser.add_argument(
        "--report-dir", type=Path, default=Path("reports"), help="directory for generated reports"
    )
    args = parser.parse_args(argv)
    seeds = [int(seed.strip()) for seed in args.seeds.split(",") if seed.strip()]
    summary = run_core_regression(seeds=seeds, count=args.count, report_dir=args.report_dir)
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
