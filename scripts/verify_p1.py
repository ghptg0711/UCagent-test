#!/usr/bin/env python3
"""Quick verification of 5-fault detection and OOO scoreboard."""

from cache_vip.ooo_scoreboard import OooScoreboard
from cache_vip.reference_model import CacheParams
from cache_vip.regression import _run_fault_detection
from cache_vip.transactions import CacheOp, CacheResponse, CacheTxn

# Test 5 fault detection modes
print("=== Fault Detection (5 modes) ===")
faults = _run_fault_detection(CacheParams())
for name, detected in faults.items():
    status = "DETECTED" if detected else "MISSED"
    print(f"  {name}: {status}")
total = sum(faults.values())
print(f"Total: {total}/{len(faults)}")
assert total == len(faults), "Not all faults detected!"
print()

# Test OOO scoreboard
print("=== Out-of-order Scoreboard Test ===")
ref = CacheParams()
ooo = OooScoreboard()

# Push 3 expected responses
txns = [
    CacheTxn(CacheOp.WRITE, addr=0x100, size=4, data=0x1111, mask=0xF, txn_id=1),
    CacheTxn(CacheOp.READ, addr=0x200, size=4, txn_id=2),
    CacheTxn(CacheOp.READ, addr=0x300, size=4, txn_id=3),
]
responses = []
for txn in txns:
    resp = CacheResponse(txn_id=txn.txn_id, data=txn.data or 0, hit=True)
    responses.append(resp)
    ooo.push_expected(txn, resp)

# Compare in reverse order (out-of-order!)
for resp in reversed(responses):
    ooo.compare_actual(resp)
    print(f"  Matched txn_id={resp.txn_id} (out-of-order)")

summary = ooo.summary()
print(f"  Matched: {summary['matched']}, Pending: {summary['pending']}")
assert summary["matched"] == 3
assert summary["pending"] == 0
print()

# Test orphan detection
print("=== OOO Orphan Detection ===")
ooo2 = OooScoreboard()
try:
    ooo2.compare_actual(CacheResponse(txn_id=999, data=0, hit=False))
    print("  FAIL: Should have raised ScoreboardMismatch")
except Exception as e:
    print(f"  Correctly detected orphan: {type(e).__name__}")
    summary2 = ooo2.summary()
    assert summary2["mismatched"] == 1

print()
print("All OOO scoreboard tests passed!")
