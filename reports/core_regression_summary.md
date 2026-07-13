# Regression Summary

Status: `PASS`

## Coverage

- Required bin coverage: `100.0%`
- Covered bins: `19/19`
- Missing bins: `none`

## Fault Detection

- read_corruption: `detected`
- partial_write_mask_drop: `detected`
- dirty_writeback_corruption: `detected`
- response_order_swap: `detected`
- tag_compare_error: `detected`
- writeback_addr_corruption: `detected`

## Required Bin Counts

| Bin | Hits |
| --- | ---: |
| `access.read_hit` | 2 |
| `access.read_miss` | 13 |
| `access.write_hit` | 5 |
| `access.write_miss` | 11 |
| `addr.line_boundary` | 1 |
| `addr.same_set` | 27 |
| `latency.long` | 9 |
| `latency.short` | 22 |
| `mask.full` | 29 |
| `mask.single` | 4 |
| `mask.sparse` | 1 |
| `op.read` | 15 |
| `op.write` | 16 |
| `replacement.clean` | 3 |
| `replacement.dirty` | 4 |
| `size.1` | 3 |
| `size.2` | 2 |
| `size.4` | 6 |
| `size.8` | 20 |

## CRV

- crv_seed_1: `300` transactions, status `PASS`, coverage `100.0%`
- crv_seed_2: `300` transactions, status `PASS`, coverage `100.0%`
- crv_seed_3: `300` transactions, status `PASS`, coverage `100.0%`
