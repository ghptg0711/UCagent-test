# Coverage Hole Attribution Report

Generated: 2026-07-13T20:32:43.681646

Total missing bins: 3

## HARD_TO_REACH (2 bins)

| Bin Name | Root Cause | Difficulty | Action |
| --- | --- | --- | --- |
| cross.replacement_type.clean_write_miss | Replacement type cross requires specific eviction scenario | ★★★★ | Add directed sequences for specific replacement scenarios |
| cross.size_mask.size1_single | Cross coverage requires size1-byte access with single mask simultaneously | ★★★ | Add directed test with size1-byte access and single mask |

### cross.replacement_type.clean_write_miss

- **Category**: HARD_TO_REACH
- **Root Cause**: Replacement type cross requires specific eviction scenario
- **Required Conditions**:
  - Specific eviction type must occur
  - Specific access type must trigger it
- **Suggested Action**: Add directed sequences for specific replacement scenarios

### cross.size_mask.size1_single

- **Category**: HARD_TO_REACH
- **Root Cause**: Cross coverage requires size1-byte access with single mask simultaneously
- **Required Conditions**:
  - Access must be exactly size1 bytes
  - Mask must be single type
  - Both conditions must occur in same transaction
- **Suggested Action**: Add directed test with size1-byte access and single mask

## CONFIG_BLOCKED (1 bins)

| Bin Name | Root Cause | Difficulty | Action |
| --- | --- | --- | --- |
| policy.replacement.fifo_eviction | FIFO eviction requires fifo replacement policy | ★★ | Run regression with replacement=fifo |

### policy.replacement.fifo_eviction

- **Category**: CONFIG_BLOCKED
- **Root Cause**: FIFO eviction requires fifo replacement policy
- **Required Conditions**:
  - Cache must be configured with fifo replacement
  - Eviction must occur
- **Suggested Action**: Run regression with replacement=fifo
