---
name: cache-verification-orchestrator
description: Orchestrates the end-to-end NutShell Cache verification workflow using UCAgent. Invoke when user starts a verification task, plans verification strategy, runs regression, prepares contest deliverables, or needs to coordinate picker/toffee/coverage/fault-injection steps together.
---

# Cache Verification Orchestrator

This skill coordinates the complete NutShell Cache automated verification workflow built on UCAgent. It is the entry point for planning, executing, and reporting cache verification tasks. Use it to decide which sub-skills to activate and in what order.

## When to Invoke

Activate this skill when the user wants to:
- Plan or kick off a NutShell Cache verification task
- Run the full regression pipeline (compile → pytest → regression → coverage)
- Prepare contest deliverables (code repo + verification report)
- Coordinate between Picker binding, Toffee env, CRV, coverage, faults, scoreboard
- Understand the project's layered architecture and where to intervene manually
- Decide which UCAgent-generated artifact needs human review/refinement

## Project Architecture (4 Layers)

| Layer | Responsibility | Location |
| --- | --- | --- |
| DUT Integration | Picker-generated sim model + Toffee drives clock/reset/signals | `rtl/dut_gen/`, `src/cache_vip/toffee_adapter.py`, `src/cache_vip/real_dut_adapter.py` |
| Protocol Adapter | Translate DUT signals into unified `CacheTxn`/`CacheResponse` | `src/cache_vip/transactions.py`, `configs/signal_map.yaml` |
| Verification Core | generator, reference model, memory agent, scoreboard, coverage, faults | `src/cache_vip/*.py` (DUT-independent) |
| Regression Report | pytest, core regression CLI, coverage/bug/report outputs | `tests/`, `scripts/`, `reports/` |

## Standard Verification Flow

1. **DUT Binding** → activate `picker-rtl-binding`: generate Python sim model from NutShell Cache RTL, confirm signal names land in `configs/signal_map.yaml`.
2. **Env Build** → activate `toffee-env-builder`: wire `ToffeeCacheAdapter` + `MemoryAgent` to drive/sample DUT signals.
3. **CRV Authoring** → activate `cache-crv-designer`: hand-write constrained random stimuli for corner cases UCAgent cannot reach.
4. **Scoreboard Check** → activate `scoreboard-engineering`: ensure comparison rules catch data/mask/writeback/order faults.
5. **Coverage Analysis** → activate `coverage-analysis`: identify uncovered bins, add directed closure, track convergence.
6. **Fault Injection** → activate `fault-injection-designer`: inject targeted bugs to prove scoreboard detection capability.
7. **Auto Refinement** → activate `llm-check-refinement`: run LLM check on AI-generated code, fix errors, improve quality.
8. **Final Submission Review** → activate `submission-review-and-grading`: grade against the official 100-point rubric, generate `docs/submission_review_report.md`, fix P0/P1 items, re-grade until 一等奖 (≥85) is stable. **Every final-submission version MUST pass this gate.**

## Execution Commands (WSL2 required)

```bash
cd /mnt/d/UCagent
source .venv/bin/activate

# Compile check
python -m compileall src tests

# Unit tests
python -m pytest tests -v --asyncio-mode=auto

# Core regression (multi-seed CRV)
PYTHONPATH=src python -m cache_vip.regression --seeds 1,2,3 --count 300 --report-dir reports

# Real DUT smoke (needs Picker/Verilator build artifacts)
PYTHONPATH=src:. python -m pytest tests/test_real_dut_smoke.py -v --asyncio-mode=auto
```

## Contest Deliverable Checklist

| Path | Content |
| --- | --- |
| `src/cache_vip/` | Reusable Cache verification core |
| `tests/` | DUT-independent unit tests + negative tests |
| `configs/` | DUT signal map samples |
| `docs/contest_statement.md` | Contest statement |
| `docs/overall_solution.md` | Overall solution |
| `docs/acceptance_document.md` | Acceptance document |
| `docs/verification_report.md` | Current verification report |
| `reports/` | Coverage, bug, AI collaboration and regression summaries |

## Developer Task Emphasis

UCAgent rapidly builds a verification prototype, but **manual intervention is required** for deep customization:
- **Constraint refinement**: hand-write complex CRV covering corner cases UCAgent cannot reach.
- **Architecture refactor**: integrate UCAgent-generated snippets into Toffee's structured framework, perform code review and refactoring.
- **Fault injection**: hand-design specific bug scenarios to validate the verification environment's detection capability.

## Key Resource Links

- UCAgent repo: https://www.gitlink.org.cn/XS-MLVP/UCAgent
- UCAgent manual: https://ucagent.open-verify.cc
- Agent Skills spec: https://agentskills.io/specification
- Base tool docs: https://ucagent.open-verify.cc

## Decision Guide: Which Sub-skill Next?

| User intent | Activate |
| --- | --- |
| "Generate Python DUT from RTL" / "Picker compile fails" | `picker-rtl-binding` |
| "Build Toffee env" / "adapter signal mismatch" | `toffee-env-builder` |
| "Add corner case stimulus" / "CRV not reaching X" | `cache-crv-designer` |
| "Coverage gap" / "add coverage bin" | `coverage-analysis` |
| "Inject bug to test scoreboard" | `fault-injection-designer` |
| "Scoreboard misses mismatch" | `scoreboard-engineering` |
| "Fix AI-generated code" / "auto-correct errors" | `llm-check-refinement` |
| "评审打分" / "能拿几等奖" / "final submission review" | `submission-review-and-grading` |
