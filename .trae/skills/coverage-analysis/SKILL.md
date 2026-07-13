---
name: coverage-analysis
description: Analyzes functional coverage for NutShell Cache verification, identifies uncovered bins, and tracks convergence. Invoke when user inspects coverage percent, finds missing bins, adds closure cases, reads reports/coverage_summary.md, or tunes the generator to raise coverage.
---

# Coverage Analysis

Functional coverage quantifies which cache behaviors the test suite has exercised. This skill covers reading coverage state, diagnosing missing bins, adding directed closure, and tracking convergence across seeds.

## When to Invoke

- Coverage percent < 100% and you need to close gaps
- `Coverage.missing()` reports unhit bins
- Need to add a new bin to `REQUIRED_BINS`
- Reading or updating `reports/coverage_summary.md`, `reports/coverage_convergence.csv`
- Tuning `GeneratorProfile` weights to raise a lagging bin
- Deciding whether a bin needs a directed case vs. higher random weight

## Coverage Model

Implemented in [src/cache_vip/coverage.py](file:///d:/UCagent-V2/UCagent-test/src/cache_vip/coverage.py):

```python
@dataclass
class Coverage:
    bins: Counter[str]
    line_bytes: int = 64
    REQUIRED_BINS = { 19 bins, see below }
```

`sample_access(txn, *, hit, evicted_dirty, evicted_clean, latency, same_set)` increments bins. The scoreboard calls it via `push_request`.

## The 19 Required Bins

| Group | Bins |
| --- | --- |
| op | `op.read`, `op.write` |
| size | `size.1`, `size.2`, `size.4`, `size.8` |
| access | `access.read_hit`, `access.read_miss`, `access.write_hit`, `access.write_miss` |
| replacement | `replacement.clean`, `replacement.dirty` |
| mask | `mask.full`, `mask.single`, `mask.sparse` |
| addr | `addr.same_set`, `addr.line_boundary` |
| latency | `latency.short`, `latency.long` |

**Closure target**: 19/19 = 100%. Current state: core directed closure reaches 100%.

## Bin Classification Logic

| Bin | Condition |
| --- | --- |
| `mask.full` | `txn.mask == (1<<size)-1` |
| `mask.single` | mask is a single power of two |
| `mask.sparse` | mask has multiple bits set but not all |
| `addr.line_boundary` | `addr % line_bytes >= line_bytes - 8` |
| `addr.same_set` | set by caller via `same_set=True` — **must use real address locality, not synthetic index modulo** |
| `latency.long` | `latency >= 8`, else `latency.short` |
| `replacement.dirty/clean` | set via `evicted_dirty` / `evicted_clean` flags |

## Gap-Closure Workflow

1. Run regression: `PYTHONPATH=src python -m cache_vip.regression --seeds 1,2,3 --count 300 --report-dir reports`
2. Read `reports/coverage_summary.md` or call `Coverage.missing()`.
3. For each missing bin, pick a closure strategy:
   - **Directed case** (preferred for rare events): add to `tests/test_directed_cases.py` and the regression's `_directed_stream`.
   - **Weight tuning** (for under-hit random bins): adjust `GeneratorProfile`.
4. Re-run multi-seed to confirm closure is stable.
5. Append a row to `reports/coverage_convergence.csv` (seed set, count, percent, missing count).

## Convergence Tracking

`reports/coverage_convergence.csv` records percent over increasing seed counts. Plot via `scripts/generate_coverage_trend.py` → `reports/coverage_convergence_trend.svg`. A healthy convergence:
- Rises monotonically.
- Reaches 100% within a small seed count for directed closure.
- Stays flat at 100% as seeds grow (no flapping).

## Adding a New Bin

1. Add the bin name to `Coverage.REQUIRED_BINS`.
2. Add sampling logic in `sample_access` (or a new `sample_*` method).
3. Call the sampler from `Scoreboard.push_request` with the right flags.
4. Add a directed case that hits the new bin.
5. Update `docs/verification_matrix.md` and the bin table in this skill.

## Critical: same_set Sampling Must Use Real Address Locality

The `addr.same_set` bin requires the caller to pass `same_set=True` when a set is revisited. **Do NOT use synthetic heuristics like `index % 7 == 0`** — this was an AI-generated bug (P1.3 fix) that caused single-seed CRV to stall at 94.7% because the marker was uncorrelated with actual address locality.

Correct pattern (implemented in `regression.py` `_run_named_stream` and `_run_enhanced_core_seed`):

```python
visited_sets: set[int] = set()
for txn in txns:
    set_idx = (txn.addr // params.line_bytes) % params.sets
    same_set = set_idx in visited_sets
    visited_sets.add(set_idx)
    cov.sample_access(txn, ..., same_set=same_set)
```

After this fix, a single CRV seed independently reaches 100% coverage (was 94.7%).

## Reports to Update

| File | When |
| --- | --- |
| `reports/coverage_summary.md` | After any regression run |
| `reports/coverage_convergence.csv` | After a convergence sweep |
| `reports/verilator_coverage/coverage_summary.json` | After real DUT Verilator coverage |
| `docs/verification_report.md` | When coverage milestone changes |

## Hand-off

After closing bins, use `fault-injection-designer` to confirm the scoreboard still detects injected bugs on the now-covered scenarios.
