# Verification Matrix: NutShell Cache

## Overview

| Spec Area | Feature | Priority | Status |
| --- | --- | --- | --- |
| Cache Read | Read hit / read miss / fill | P0 | Covered |
| Cache Write | Write hit / write miss / partial mask | P0 | Covered |
| Replacement | LRU, FIFO, replacement pressure | P0 | Covered |
| Write-back | Clean eviction and dirty eviction | P0 | Covered |
| Bus Interface | SimpleBus ready/valid smoke | P0 | Covered |
| Corner Cases | Line boundary, same-set storm, reset recovery | P1 | Covered |
| Fault Injection | Read corruption, mask drop, writeback corruption, order swap, tag compare | P1 | Covered |
| RTL Bug Evidence | BUG-010 LRU defect, BUG-011 dirty eviction deadlock | P0 | Covered |

## Feature To Test Mapping

| Feature | Test File | Test Function | Type |
| --- | --- | --- | --- |
| Read hit / read miss | `tests/test_dut_smoke.py` | smoke read tests | Directed |
| Write hit / write miss | `tests/test_dut_smoke.py` | smoke write tests | Directed |
| Random read/write traffic | `tests/test_generator_scoreboard.py` | generator + scoreboard tests | CRV |
| Partial write mask | `tests/test_edge_cases.py` | `TestMixedSizeAccess::test_mixed_sizes_same_line` | Corner |
| Line boundary and alignment | `tests/test_edge_cases.py` | `TestAlignmentStress::*` | Corner |
| Dirty replacement pressure | `tests/test_edge_cases.py` | `TestReplacementPressure::test_continuous_replacement` | Corner |
| CPU request during replacement | `tests/test_edge_cases.py` | `TestReplacementPressure::test_replacement_interrupted_by_new_request` | Corner |
| LRU repeated hot-line access | `tests/test_edge_cases.py` | `TestReplacementPressure::test_lru_counter_saturation` | Corner |
| FIFO replacement behavior | `tests/test_edge_cases.py` | `TestFIFOEdge::test_fifo_ordering` | Directed |
| No-write-allocate behavior | `tests/test_edge_cases.py` | `TestNoWriteAllocateEdge::test_no_write_allocate_read_then_write` | Directed |
| BUG-010 LRU RTL defect | `tests/test_directed_cases.py` | `TestDirectedCases::test_lru_eviction_order_bug010` | Bug Evidence |
| BUG-011 dirty eviction deadlock | `tests/test_directed_cases.py` | `TestDirectedCases::test_dirty_eviction_fill_bug011` | Bug Evidence |
| Real DUT handshake | `tests/test_real_dut_smoke.py` | all smoke tests | Real DUT |
| Fault injection modes | `tests/test_regression.py` | fault regression tests | Negative |
| Out-of-order matching | `tests/test_ooo_scoreboard.py` | OOO scoreboard tests | Scoreboard |

## Coverage Cross Matrix

| Cross | Dimensions | Evidence |
| --- | --- | --- |
| Read x hit/miss | operation result | functional coverage bins `access.read_hit`, `access.read_miss` |
| Write x hit/miss | operation result | functional coverage bins `access.write_hit`, `access.write_miss` |
| Access size x alignment | size and offset | `TestMixedSizeAccess`, `TestAlignmentStress` |
| Replacement x dirty state | victim state | `replacement.clean`, `replacement.dirty` bins |
| Same-set traffic x eviction | set locality and replacement | `addr.same_set` plus replacement bins |

## Known Limits And Justification

| Item | Status | Justification |
| --- | --- | --- |
| Hardware snoop interruption | Not applicable | The submitted NutShell L1 Cache interface does not expose a hardware snoop channel. CPU-side interruption during replacement is covered instead. |
| AXI DECERR/SLVERR | Not applicable | This DUT uses SimpleBus-style responses without AXI error response encoding. Timeout/deadlock behavior is covered. |
| RTL fixes for BUG-010/011 | DUT defect confirmed | Verification environment detects and documents the defects; RTL redesign is upstream work. |
