# Semantic Refactoring Metrics Report

Generated: 2026-07-13T20:21:36.579829

## Overall Metrics

- Total refactoring events: 14
- Total entropy score: 10.85
- Average entropy per event: 0.78
- Architecture-level events: 9 (64.3%)
- Implementation-level events: 5
- Syntax-level events: 0

## Module-level Metrics

| Module | Total | Architecture | Implementation | Syntax | Avg Entropy |
| --- | --- | --- | --- | --- | --- |
| scoreboard | 2 | 2 | 0 | 0 | 0.9 |
| reference_model | 3 | 2 | 1 | 0 | 0.77 |
| coverage | 2 | 1 | 1 | 0 | 0.68 |
| ooo_scoreboard | 2 | 2 | 0 | 0 | 0.9 |
| regression | 2 | 1 | 1 | 0 | 0.8 |
| faults | 1 | 1 | 0 | 0 | 0.8 |
| real_dut_adapter | 1 | 0 | 1 | 0 | 0.65 |
| toffee_adapter | 1 | 0 | 1 | 0 | 0.55 |

## Architecture-level Refactoring Events

- **src/cache_vip/scoreboard.py**: Fixed circular reasoning: Scoreboard now uses independent good_ref + faulty_ref pattern instead of comparing ref.access() to itself
  - Type: CONTROL_FLOW_RESTRUCTURE
  - Location: compare_response method
  - Entropy: 0.95

- **src/cache_vip/scoreboard.py**: Added comprehensive field comparison: hit/miss, dirty eviction, writeback addr/data, error fields
  - Type: ASSERTION_LOGIC
  - Location: compare_response method
  - Entropy: 0.85

- **src/cache_vip/reference_model.py**: Fixed LRU recency tracking: LRU now properly maintains access order instead of simple round-robin
  - Type: STATE_MACHINE
  - Location: _touch method
  - Entropy: 0.9

- **src/cache_vip/reference_model.py**: Added dirty bit tracking and writeback mechanism for dirty evictions
  - Type: DATA_STRUCTURE
  - Location: access method
  - Entropy: 0.8

- **src/cache_vip/coverage.py**: Extended coverage model with 12 cross-coverage bins (size×mask, replacement×type, access×latency, policy, address pattern)
  - Type: NEW_CLASS
  - Location: Coverage class
  - Entropy: 0.85

- **src/cache_vip/ooo_scoreboard.py**: Added independent writeback event stream tracking with out-of-order matching capability
  - Type: NEW_CLASS
  - Location: WritebackEvent class
  - Entropy: 0.92

- **src/cache_vip/ooo_scoreboard.py**: Implemented txn_id-based out-of-order matching with orphan/duplicate/reorder detection
  - Type: CONTROL_FLOW_RESTRUCTURE
  - Location: compare_actual method
  - Entropy: 0.88

- **src/cache_vip/regression.py**: Refactored fault detection from definitionally-true pattern to end-to-end good_ref + faulty_ref + ScoreboardMismatch pattern
  - Type: CONTROL_FLOW_RESTRUCTURE
  - Location: _detect_* functions
  - Entropy: 0.9

- **src/cache_vip/faults.py**: Added corrupt_writeback_addr() fault injection for writeback address generation errors
  - Type: NEW_FUNCTION
  - Location: FaultInjector class
  - Entropy: 0.8
