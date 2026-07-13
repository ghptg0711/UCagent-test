---
name: scoreboard-engineering
description: Implements and debugs the NutShell Cache scoreboard comparison rules. Invoke when user adds a new comparison field, debugs a ScoreboardMismatch, fixes a detection gap where a fault is not caught, or refactors expected-response queue handling.
---

# Scoreboard Engineering

The scoreboard is the oracle: it compares DUT responses against the reference model and raises `ScoreboardMismatch` on any divergence. This skill covers the comparison contract, adding new checks, and diagnosing escapes.

## When to Invoke

- A fault is injected but the scoreboard does NOT raise (detection gap)
- Need to add a comparison field (e.g., eviction address, error flag)
- Debug a flaky `ScoreboardMismatch` (order, timeout, queue drift)
- Refactor the expected-response queue (in-order vs. out-of-order)
- Add an OOO scoreboard variant for memory-side reordering

## Scoreboard Contract

Implemented in [src/cache_vip/scoreboard.py](file:///d:/UCagent-V2/UCagent-test/src/cache_vip/scoreboard.py):

```python
@dataclass
class Scoreboard:
    reference: ReferenceCache
    coverage: Coverage              # auto-created from reference params
    expected: list[CacheResponse]   # FIFO of pending expected responses

    def push_request(txn, *, latency, same_set) -> CacheResponse
    def compare_response(txn, actual) -> None     # raises on mismatch
    def observe_transaction(txn, actual, *, latency) -> None  # push + compare
```

Flow: `push_request` runs the reference model and queues the expected response (also sampling coverage). `compare_response` pops the FIFO head and checks each field. `observe_transaction` is the convenience wrapper used by tests.

## Comparison Checks (current)

`compare_response` raises `ScoreboardMismatch` if any of these differ between expected and actual:

1. `txn_id` (order — FIFO head must match)
2. `hit` (hit/miss classification)
3. `data` for READ ops (read data integrity)
4. `evicted_dirty` (dirty eviction flag)
5. `writeback_addr` (writeback target address)
6. `writeback_data` (writeback payload)
7. `error` (error flag)

## Adding a New Check

1. Add the field to `CacheResponse` in `src/cache_vip/transactions.py`.
2. Populate it in `ReferenceCache.access` (the reference must produce it).
3. Add a comparison block in `compare_response`:
   ```python
   if expected.<field> != actual.<field>:
       raise ScoreboardMismatch(f"<field> mismatch txn_id={txn.txn_id}: ...")
   ```
4. Add a fault that corrupts the field (`fault-injection-designer`) and a negative test.
5. Update the comparison-checks list above.

## Common Escapes & Fixes

| Symptom | Cause | Fix |
| --- | --- | --- |
| Fault injected, no mismatch | field not compared | add check (see above) |
| Order swap not caught | FIFO not strict | ensure `expected.pop(0)` and txn_id compare |
| Flaky mismatch on latency | latency sampled into coverage but not compared | latency is a coverage bin, not a correctness field — do not compare |
| Mismatch on every read | reference model params ≠ DUT params | align `CacheParams` with DUT config |
| Writeback mismatch on clean eviction | reference sets writeback=None, DUT drives 0 | normalize None vs 0 in adapter before compare |

## Out-of-Order Variant

`src/cache_vip/ooo_scoreboard.py` provides an OOO scoreboard for memory-side reordering: it matches responses by `txn_id`/`source_id` instead of FIFO order. Use it when the DUT memory path can reorder responses. Switch via the adapter; do not run both simultaneously on the same queue.

## Timeout & Queue Health

- `response_timeout` (adapter) guards hung handshakes.
- If `expected` grows unbounded, the DUT is dropping responses — add a `len(expected) > N` assertion in regression.
- After a regression run, `expected` should be empty; assert this in tests.

## Testing the Scoreboard Itself

- Positive: run `CacheGenerator` stream through `observe_transaction` with reference responses → no raise.
- Negative: for each `FaultInjector` method, assert `ScoreboardMismatch` (see `fault-injection-designer`).
- Self-consistency tests live in `tests/test_scoreboard_*` and `tests/test_ooo_scoreboard.py`.

## Hand-off

Once comparison is solid, run `coverage-analysis` to confirm coverage, and use `llm-check-refinement` to review any AI-generated scoreboard changes.
