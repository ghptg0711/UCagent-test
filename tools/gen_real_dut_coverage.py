"""Run real DUT transactions and generate Verilator coverage report.

Usage (in WSL2):
    cd /mnt/d/UCagent
    PYTHONPATH=src:. python3 tools/gen_real_dut_coverage.py
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from cache_vip.dut_regression import DUTRegressionRunner
from cache_vip.generator import CacheGenerator, GeneratorProfile
from cache_vip.real_dut_adapter import create_real_dut_adapter
from cache_vip.real_dut_config import REAL_DUT_CACHE_PARAMS
from cache_vip.reference_model import ReferenceCache
from cache_vip.scoreboard import Scoreboard
from cache_vip.transactions import CacheOp, CacheTxn

COVERAGE_FILE = "reports/real_dut_coverage.dat"
REPORT_DIR = Path("reports/real_dut_coverage")


async def main() -> None:
    # Ensure report dir exists
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("Creating real DUT adapter (functional coverage mode)")
    adapter = await create_real_dut_adapter()
    await adapter.reset(clear_memory=True)
    runner = DUTRegressionRunner(
        adapter, scoreboard=Scoreboard(ReferenceCache(REAL_DUT_CACHE_PARAMS))
    )
    print("DUT created and reset OK")

    # Run directed smoke tests
    txn_id = 1
    txns = [
        # Basic read miss
        CacheTxn(CacheOp.READ, addr=0x00, size=8, txn_id=txn_id),
        # Write then read
        CacheTxn(
            CacheOp.WRITE, addr=0x00, size=8, data=0x1122334455667788, mask=0xFF, txn_id=txn_id + 1
        ),
        CacheTxn(CacheOp.READ, addr=0x00, size=8, txn_id=txn_id + 2),
        # Partial write with mask
        CacheTxn(CacheOp.WRITE, addr=0x04, size=4, data=0xAABBCCDD, mask=0b0101, txn_id=txn_id + 3),
        CacheTxn(CacheOp.READ, addr=0x00, size=8, txn_id=txn_id + 4),
        # Read miss then hit (same line)
        CacheTxn(CacheOp.READ, addr=0x100, size=8, txn_id=txn_id + 5),
        CacheTxn(CacheOp.READ, addr=0x100, size=8, txn_id=txn_id + 6),
    ]
    txn_id += 7

    print(f"\nRunning {len(txns)} directed transactions...")
    for txn in txns:
        resp = await runner.execute(txn)
        print(
            f"  txn {txn.txn_id}: op={txn.op.name} addr=0x{txn.addr:x} -> "
            f"data=0x{resp.data:x} hit={resp.hit}"
        )
    print("Directed transactions done")

    # Run CRV transactions
    params = REAL_DUT_CACHE_PARAMS
    gen = CacheGenerator(params, seed=42, profile=GeneratorProfile(uncached_weight=0))
    crv_txns = gen.random_stream(200)
    print(f"\nRunning {len(crv_txns)} CRV transactions...")
    for i, txn in enumerate(crv_txns):
        await runner.execute(txn)
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(crv_txns)} transactions done")
    print("CRV transactions done")

    # Flush coverage
    print("\nFinishing DUT...")
    adapter.finish()
    print("DUT finished")

    # Generate functional coverage summary
    functional_coverage = runner.coverage.summary()
    summary = {
        "dut_type": "Real NutShell Cache (DUTRealNutShellCache)",
        "total_transactions": len(txns) + len(crv_txns),
        "directed_transactions": len(txns),
        "crv_transactions": len(crv_txns),
        "crv_seed": 42,
        "verilator_coverage_available": False,
        "functional_coverage": functional_coverage,
        "coverage_source": "DUT-observed response fields only",
        "unobservable_fields": ["clean_eviction", "writeback_data"],
        "exclusion_justification": (
            "Verilator line/branch/FSM/toggle coverage not available because "
            "the pre-compiled DUT .so was not built with --coverage flag. "
            "DUT-observed functional coverage is reported without inventing "
            "unobservable hit/replacement events. "
            "To enable code coverage, recompile NutShell RTL with: "
            "verilator --cc --coverage -Wno-fatal NutShellCache.v"
        ),
        "status": (
            "PASS"
            if functional_coverage["coverage_percent"] >= 90.0
            else "INCOMPLETE_COVERAGE"
        ),
    }
    summary_path = REPORT_DIR / "real_dut_coverage_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSummary written to {summary_path}")
    print("\n=== Real DUT Coverage Generation Complete ===")
    if summary["status"] != "PASS":
        raise SystemExit(
            "Real DUT coverage is below 90% because required DUT events are not observable"
        )


if __name__ == "__main__":
    asyncio.run(main())
