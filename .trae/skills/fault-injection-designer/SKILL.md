---
name: fault-injection-designer
description: Designs fault injection scenarios to validate the scoreboard's detection capability for NutShell Cache. Invoke when user injects read-bit flips, mask drops, writeback corruption, response-order swaps, tag-match errors, or validates that the scoreboard raises ScoreboardMismatch on each fault.
---

# Fault Injection Designer

Fault injection proves the verification environment can actually catch bugs — not just pass on a correct DUT. This skill covers the five built-in fault types, how to author new ones, and how to wire negative tests.

## When to Invoke

- Validate the scoreboard detects a specific bug class
- Add a new fault type beyond the 5 built-ins
- Author a negative test that asserts `ScoreboardMismatch` is raised
- Diagnose a fault that the scoreboard fails to catch (detection gap)
- Update `reports/bug_tracker.md` with a new injected-bug entry
- Prepare contest evidence that the env has检出能力 (detection capability)

## Built-in Fault Types

Implemented in [src/cache_vip/faults.py](file:///d:/UCagent-V2/UCagent-test/src/cache_vip/faults.py):

| Fault | Method | Models | Scoreboard check that catches it |
| --- | --- | --- | --- |
| Read data bit flip | `flip_read_bit(resp, bit)` | data corruption on read path | read data mismatch |
| Write mask bit drop | `drop_mask_bit(txn, bit)` | partial-write mask lost | read-back data mismatch |
| Writeback byte corruption | `corrupt_writeback_byte(resp, byte_index)` | dirty eviction data broken | writeback data mismatch |
| Response order swap | `swap_order(responses)` | out-of-order / transaction ID swap | txn_id order mismatch |
| Tag match flip | `flip_tag_match(resp)` | tag comparator error | hit/miss mismatch |

**Current detection result**: 5/5 faults detected (see `reports/core_regression_summary.md`).

## Authoring a Negative Test

Pattern used in `tests/`:

```python
from cache_vip.generator import CacheGenerator
from cache_vip.scoreboard import Scoreboard, ScoreboardMismatch
from cache_vip.faults import FaultInjector
import pytest

def test_read_bit_flip_detected():
    gen = CacheGenerator(seed=1)
    sb = Scoreboard()
    txn = gen.random_txn()                      # a write so data is observable later
    expected = sb.push_request(txn)
    faulty = FaultInjector.flip_read_bit(expected, bit=3)
    with pytest.raises(ScoreboardMismatch):
        sb.compare_response(txn, faulty)
```

Rules:
- A negative test MUST raise `ScoreboardMismatch`; if it passes, that's a detection gap — fix the scoreboard (see `scoreboard-engineering`).
- Each fault type needs at least one negative test.
- Record the fault in `reports/bug_tracker.md` with: id, type, description, detection status, repro sequence.

## Designing a New Fault

1. Identify the cache behavior to corrupt (e.g., LRU victim selection, line fill data, uncached bypass).
2. Add a `@staticmethod` to `FaultInjector` returning a new `CacheTxn`/`CacheResponse` via `dataclasses.replace`.
3. Determine which `Scoreboard.compare_response` check catches it. If none, add a check (and a reference-model field if needed).
4. Add a negative test asserting `ScoreboardMismatch`.
5. Register the fault in `run_core_regression._run_fault_detection` so it appears in the regression summary.

## Fault Detection in Regression

`run_core_regression` calls `_run_fault_detection(params)` which exercises each fault type and returns a `{fault_name: bool}` dict. The overall regression `PASS` requires `all(faults.values())`. If a fault regresses to undetected, regression fails fast.

## Bug Tracker Entry Format

`reports/bug_tracker.md`:

```markdown
### BUG-<id>: <short title>
- Type: read_corruption | mask_drop | writeback_corruption | order_swap | tag_error | <new>
- Injected by: FaultInjector.<method>
- Detection: ScoreboardMismatch (<which check>)
- Repro: seed=<n>, txn_id=<id>, addr=0x.., description
- Status: detected | escaped (gap)
```

## Hand-off

After a new fault is added and detected, re-run `coverage-analysis` to ensure the fault's scenario is still covered, and update `docs/verification_report.md` with the new detection count.
