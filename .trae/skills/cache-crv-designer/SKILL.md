---
name: cache-crv-designer
description: Designs and hand-authors constrained-random stimuli (CRV) for NutShell Cache corner cases that UCAgent cannot reach. Invoke when user writes directed/CRV sequences, refines generator profiles, covers replacement/partial-write/boundary/uncached scenarios, or strengthens constraints for corner cases.
---

# Cache CRV Designer

Constrained Random Verification (CRV) is the core of modern verification. UCAgent generates a baseline stream, but **manual refinement is required** for corner cases the agent cannot reach. This skill covers authoring directed sequences and tuning `CacheGenerator` profiles.

## When to Invoke

- Add directed sequences for replacement, dirty/clean eviction, partial write, same-set pressure
- Refine `GeneratorProfile` weights to hit specific coverage bins
- Author corner-case streams: line boundary, extreme alignment, RAW hazard, uncached MMIO
- Strengthen constraints after a coverage gap is reported by `coverage-analysis`
- Convert a reproducible bug sequence into a regression directed case

## Generator Architecture

Implemented in [src/cache_vip/generator.py](file:///d:/UCagent-V2/UCagent-test/src/cache_vip/generator.py):

```python
@dataclass(frozen=True)
class GeneratorProfile:
    read_weight: int = 55
    write_weight: int = 45
    hot_set_weight: int = 35      # bias toward a small hot set
    boundary_weight: int = 10     # line-boundary addresses
    uncached_weight: int = 5      # uncached/MMIO traffic
```

`CacheGenerator` exposes:
- `random_txn()` / `random_stream(count)` — weighted CRV
- `replacement_sequence(set_idx, dirty=)` — fill a set beyond `ways` to force eviction
- `partial_write_sequence(base_addr)` — full + sub-line writes with masks, then read-back
- `mixed_corner_stream()` — composite of partial write + dirty + clean replacement
- `replacement_sequence_with_lru_check(set_idx)` — validates LRU victim selection

## CacheParams (drives addressing)

From [src/cache_vip/reference_model.py](file:///d:/UCagent-V2/UCagent-test/src/cache_vip/reference_model.py): default `CacheParams` defines `line_bytes`, `sets`, `ways`, `offset_bits`, `tag_bits`. Address decode:
- `offset = addr % line_bytes`
- `set_idx = (addr // line_bytes) % sets`
- `tag = addr // (line_bytes * sets)`

## Corner-Case Catalog (hand-authored)

| Scenario | Why it matters | Sequence shape |
| --- | --- | --- |
| Same-set multi-tag replacement | LRU victim selection | write `ways+1` distinct tags to one set, read back tag 0 |
| Dirty eviction writeback | writeback data integrity | write tag A dirty, evict with tag B, check writeback addr/data |
| Clean eviction (no writeback) | avoid spurious writeback | read-fill tag A, evict with tag B, assert no writeback |
| Partial write byte-mask merge | mask drop bug | full-line write 0xFF, sub-line writes with sparse masks, read-back |
| Line boundary access | cross-line addressing | access `base-1`, `base`, `base+line_bytes-1`, `base+line_bytes` |
| Size sweep 1B/2B/4B/8B | width handling | same addr, each size, verify read data |
| Uncached / MMIO | bypass cache path | set `uncached=True`, expect direct memory response |
| RAW hazard | read-after-write coherence | write then immediate read same addr |
| Memory latency stress | backpressure tolerance | vary `ScriptedMemoryAgent` latency short/long |
| High miss rate | replacement pressure | random stream over address space >> cache capacity |

## Authoring a New Directed Sequence

1. Identify the bin(s) it must close (see `coverage-analysis`).
2. Build the sequence using `_make(...)` helpers so `txn_id` is monotonic.
3. Add a unit test in `tests/test_directed_cases.py` that runs it through `Scoreboard` against the reference model (self-consistency).
4. Add a **negative** test variant that injects a fault (`fault-injection-designer`) and asserts `ScoreboardMismatch` is raised.
5. Register the sequence in `mixed_corner_stream()` or a new `corner_*` method if it should appear in CRV closure.

## Profile Tuning Strategy

- A bin stays at 0 → add a directed closure case (deterministic), do not rely on random.
- A bin is hit but rarely → raise its weight in `GeneratorProfile` (e.g. `boundary_weight`).
- Replacement bins lag → increase `hot_set_weight` so the same set is revisited.
- Uncached bin lags → raise `uncached_weight` (keep small to avoid dominating).
- Always re-run multi-seed (≥3) to confirm closure is not seed-lucky.

## Reproducibility Rules

- Every CRV run must accept a `seed` and record it in the report.
- A failing sequence must be dumped as a directed case under `tests/` with the exact txn list.
- Never use module-level `random`; always use the generator's `self.random`.

## Critical: same_set Coverage Sampling Must Use Real Address Locality

The `addr.same_set` coverage bin is sampled by the regression runner (not the generator). A common AI-generated mistake is to use a synthetic heuristic like `same_set = index % 7 == 0`, which is uncorrelated with actual address locality and causes single-seed CRV to stall at 94.7%.

**Correct pattern** (implemented in `regression.py`): maintain a `visited_sets` set; when a set is revisited, mark `same_set=True`. After this fix (P1.3), single-seed CRV independently reaches 100% coverage without directed-case assistance.

When authoring new CRV streams or regression runners, always sample `same_set` from real address locality, never from index modulo.

## Hand-off

After authoring, run `coverage-analysis` to confirm bins close, then use `fault-injection-designer` to validate the scoreboard still detects corruption on the new sequences.
