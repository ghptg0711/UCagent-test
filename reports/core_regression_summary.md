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

## Required Bin Counts

| Bin | Hits |
| --- | ---: |
| `access.read_hit` | 2 |
| `access.read_miss` | 8 |
| `access.write_hit` | 4 |
| `access.write_miss` | 5 |
| `addr.line_boundary` | 1 |
| `addr.same_set` | 12 |
| `latency.long` | 7 |
| `latency.short` | 12 |
| `mask.full` | 17 |
| `mask.single` | 1 |
| `mask.sparse` | 1 |
| `op.read` | 10 |
| `op.write` | 9 |
| `replacement.clean` | 2 |
| `replacement.dirty` | 2 |
| `size.1` | 2 |
| `size.2` | 2 |
| `size.4` | 1 |
| `size.8` | 14 |

## CRV

- crv_seed_1: `300` transactions, status `PASS`, coverage `100.0%`
- crv_seed_2: `300` transactions, status `PASS`, coverage `100.0%`
- crv_seed_3: `300` transactions, status `PASS`, coverage `100.0%`
