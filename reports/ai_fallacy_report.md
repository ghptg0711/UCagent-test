# AI Fallacy Detection Report

Generated: 2026-07-13T20:31:07.075536

Scanned files: 36
Total findings: 123

## CIRCULAR_REASONING (1 findings)

| File | Line | Severity | Description |
| --- | --- | --- | --- |
| test_dut_smoke.py:42 | 42 | HIGH | Reference Model may be calling DUT internal signals |

## ASYNC_TIMING (2 findings)

| File | Line | Severity | Description |
| --- | --- | --- | --- |
| real_dut_adapter.py:73 | 73 | MEDIUM | Missing await on async reset/clock operation |
| real_dut_adapter.py:75 | 75 | MEDIUM | Missing await on async reset/clock operation |

## BOUNDARY_MAGIC_NUMBER (118 findings)

| File | Line | Severity | Description |
| --- | --- | --- | --- |
| coverage.py:63 | 63 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| cross_validation.py:265 | 265 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| fallacy_detector.py:62 | 62 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| fallacy_detector.py:62 | 62 | MEDIUM | Hardcoded magic number 512 not tied to parameter |
| fallacy_detector.py:62 | 62 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| fallacy_detector.py:62 | 62 | MEDIUM | Hardcoded magic number 8192 not tied to parameter |
| faults.py:30 | 30 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| generator.py:94 | 94 | MEDIUM | Hardcoded magic number 8192 not tied to parameter |
| generator.py:211 | 211 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| generator.py:75 | 75 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| memory_agent.py:105 | 105 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| real_dut_config.py:7 | 7 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| reference_model.py:18 | 18 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| reference_model.py:20 | 20 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| regression.py:336 | 336 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| regression.py:495 | 495 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| regression.py:500 | 500 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| regression.py:571 | 571 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| regression.py:576 | 576 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| regression.py:353 | 353 | MEDIUM | Hardcoded magic number 8192 not tied to parameter |
| regression.py:360 | 360 | MEDIUM | Hardcoded magic number 8192 not tied to parameter |
| rtl_trajectory.py:99 | 99 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| mock_dut.py:49 | 49 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| mock_dut.py:49 | 49 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| mock_dut.py:59 | 59 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| mock_dut.py:61 | 61 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| mock_dut.py:66 | 66 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| mock_dut.py:70 | 70 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| mock_dut.py:72 | 72 | MEDIUM | Hardcoded magic number 512 not tied to parameter |
| mock_dut.py:73 | 73 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| mock_dut.py:77 | 77 | MEDIUM | Hardcoded magic number 512 not tied to parameter |
| test_coverage_trend.py:48 | 48 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_coverage_trend.py:52 | 52 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_directed_cases.py:376 | 376 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_directed_cases.py:138 | 138 | MEDIUM | Hardcoded magic number 8192 not tied to parameter |
| test_directed_cases.py:117 | 117 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_directed_cases.py:186 | 186 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_directed_cases.py:213 | 213 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_directed_cases.py:223 | 223 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_directed_cases.py:240 | 240 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_directed_cases.py:299 | 299 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_directed_cases.py:313 | 313 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_directed_cases.py:318 | 318 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_directed_cases.py:342 | 342 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_directed_cases.py:373 | 373 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_directed_cases.py:296 | 296 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_directed_cases.py:297 | 297 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_directed_cases.py:324 | 324 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_directed_cases.py:351 | 351 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_dut_smoke.py:50 | 50 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_dut_smoke.py:63 | 63 | MEDIUM | Hardcoded magic number 8192 not tied to parameter |
| test_dut_smoke.py:67 | 67 | MEDIUM | Hardcoded magic number 8192 not tied to parameter |
| test_edge_cases.py:245 | 245 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_edge_cases.py:195 | 195 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:198 | 198 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:281 | 281 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:303 | 303 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:308 | 308 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:339 | 339 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_edge_cases.py:344 | 344 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_edge_cases.py:352 | 352 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_edge_cases.py:92 | 92 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:97 | 97 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:109 | 109 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:114 | 114 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:117 | 117 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:210 | 210 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:215 | 215 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:224 | 224 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:229 | 229 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:243 | 243 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:243 | 243 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:270 | 270 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:359 | 359 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:380 | 380 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:384 | 384 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:389 | 389 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:400 | 400 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:405 | 405 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:416 | 416 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:421 | 421 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:425 | 425 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:430 | 430 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:438 | 438 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:452 | 452 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:522 | 522 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:553 | 553 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:554 | 554 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:560 | 560 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:564 | 564 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:583 | 583 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:591 | 591 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:101 | 101 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:121 | 121 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:364 | 364 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_edge_cases.py:274 | 274 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_generator_scoreboard.py:95 | 95 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_generator_scoreboard.py:44 | 44 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_generator_scoreboard.py:45 | 45 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_ooo_scoreboard.py:157 | 157 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_ooo_scoreboard.py:190 | 190 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_ooo_scoreboard.py:207 | 207 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_ooo_scoreboard.py:208 | 208 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_ooo_scoreboard.py:116 | 116 | MEDIUM | Hardcoded magic number 512 not tied to parameter |
| test_ooo_scoreboard.py:178 | 178 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_ooo_scoreboard.py:185 | 185 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_ooo_scoreboard.py:210 | 210 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_ooo_scoreboard.py:31 | 31 | MEDIUM | Hardcoded magic number 512 not tied to parameter |
| test_ooo_scoreboard.py:186 | 186 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_ooo_scoreboard.py:193 | 193 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_real_dut_adapter_unit.py:153 | 153 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_real_dut_adapter_unit.py:49 | 49 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_real_dut_adapter_unit.py:117 | 117 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_real_dut_adapter_unit.py:151 | 151 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_real_dut_adapter_unit.py:165 | 165 | MEDIUM | Hardcoded magic number 64 not tied to parameter |
| test_real_dut_smoke.py:63 | 63 | MEDIUM | Hardcoded magic number 4096 not tied to parameter |
| test_real_dut_smoke.py:75 | 75 | MEDIUM | Hardcoded magic number 8192 not tied to parameter |
| test_real_dut_smoke.py:78 | 78 | MEDIUM | Hardcoded magic number 8192 not tied to parameter |

## WEAK_ASSERTION (2 findings)

| File | Line | Severity | Description |
| --- | --- | --- | --- |
| test_edge_cases.py:374 | 374 | MEDIUM | Weak assertion: assert all_dirty |
| test_generator_scoreboard.py:21 | 21 | MEDIUM | Weak assertion: assert saw_dirty_eviction |

## Summary

- HIGH severity: 1
- MEDIUM severity: 122
- LOW severity: 0

⚠️ AI fallacies detected. Please review and fix before submission.