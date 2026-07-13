---
name: llm-check-refinement
description: Runs automatic error correction and quality refinement on UCAgent-generated verification code for NutShell Cache. Invoke when user wants to auto-fix errors in AI-generated code, run LLM Check & Refinement, improve verification quality, review UCAgent artifacts, or iterate code until tests pass.
---

# LLM Check & Refinement (Auto-Correct & Improve)

UCAgent's "LLM Check & Refinement" capability (see https://ucagent.open-verify.cc/content/02_usage/06_llm_check/) automatically checks AI-generated verification artifacts and refines them toward correctness and higher quality. This skill operationalizes that loop inside this repo: detect errors → propose fixes → apply → re-test → iterate until green.

## When to Invoke

- UCAgent generated a code fragment that fails compile or tests
- User asks to "auto-correct", "fix errors", "improve", or "refine" AI-generated code
- A regression run failed and the cause is in AI-authored code
- Need to iterate a generated component (generator/scoreboard/adapter) until `pytest` + `regression` pass
- Want to raise verification quality (more bins, stronger checks, better corner coverage)
- Reviewing UCAgent artifacts before human code review

## The Refinement Loop

Repeat until all gates pass:

1. **Detect** — run the gate and capture the failure signature.
   ```bash
   cd /mnt/d/UCagent && source .venv/bin/activate
   python -m compileall src tests 2>&1 | tee /tmp/compile.log
   python -m pytest tests -v --asyncio-mode=auto 2>&1 | tee /tmp/pytest.log
   PYTHONPATH=src python -m cache_vip.regression --seeds 1,2,3 --count 300 --report-dir reports 2>&1 | tee /tmp/regr.log
   ```
2. **Classify** — map the failure to a category (table below).
3. **Localize** — identify the exact file/line using the traceback and the layered architecture (do not patch the wrong layer).
4. **Propose fix** — smallest change that addresses root cause; respect the layering rules.
5. **Apply** — edit the file.
6. **Re-test** — re-run the failing gate only, then the full loop.
7. **Record** — append the iteration to `reports/ai_collaboration_log.md`.

## Failure Classification & Fix Map

| Category | Signature | Root layer | Fix approach |
| --- | --- | --- | --- |
| Syntax / import | `SyntaxError`, `ImportError`, `ModuleNotFoundError` | any | fix typo / add `__init__.py` / fix PYTHONPATH |
| Type / attribute | `AttributeError`, `TypeError` | core/adapter | align field names with `CacheTxn`/`CacheResponse` dataclasses |
| Signal mismatch | adapter drives wrong pin | DUT integration | fix `SignalMap` in `configs/signal_map*.yaml`, not the core |
| NutShell cmd encoding | write treated as read | adapter | set `cpu_req_cmd`, decode in adapter |
| Scoreboard false negative | fault not detected | scoreboard | add/fix comparison check (see `scoreboard-engineering`) |
| Coverage gap | `missing` bins | generator/coverage | add directed case or tune `GeneratorProfile` (see `coverage-analysis`) |
| Non-determinism | seed-dependent pass | generator | remove module-level `random`; use `self.random` |
| Timeout | `response_timeout` hit | adapter | check handshake / backpressure / memory agent drain |
| Queue drift | `expected` not empty | scoreboard | response dropped by DUT or adapter; trace txn_id |

## Layering Rules (must respect during refinement)

- Signal names → only in `SignalMap` + adapter.
- Transaction shape → only in `transactions.py`.
- Comparison logic → only in `scoreboard.py` / `ooo_scoreboard.py`.
- Coverage sampling → only in `coverage.py`, invoked by scoreboard.
- Stimulus authoring → only in `generator.py` + `tests/`.

Never patch a signal name inside the generator or scoreboard to "make it pass".

## Quality Improvement (beyond fixing errors)

After gates are green, optionally improve:
- Add a directed corner-case sequence (`cache-crv-designer`).
- Add a coverage bin and closure case (`coverage-analysis`).
- Add a fault + negative test (`fault-injection-designer`).
- Strengthen a scoreboard check (`scoreboard-engineering`).
Each improvement must keep all gates green and update the relevant report.

## AI Collaboration Log

Append to `reports/ai_collaboration_log.md` after each refinement iteration:

```markdown
### <timestamp> — <component>
- Trigger: <compile | pytest | regression | manual>
- Failure: <one-line summary>
- Root cause: <layer + file>
- Fix: <one-line description>
- Gates after: compile=PASS pytest=PASS regression=PASS coverage=100% faults=5/5
- Human review: pending | approved | needs-work
```

## Stop Criteria

Stop the loop when ALL hold:
- `compileall` clean
- `pytest` all pass
- `run_core_regression` status=PASS, coverage≥90% (target 100%), faults all detected
- No new files created unless necessary
- Changes recorded in the AI collaboration log

If after 3 iterations a gate still fails, escalate to human review — do not keep patching blindly.

## Reference

- UCAgent LLM Check & Refinement: https://ucagent.open-verify.cc/content/02_usage/06_llm_check/
- UCAgent human-collaboration mode: https://ucagent.open-verify.cc/content/02_usage/02_assit/
- Checkers (custom validation hooks): https://ucagent.open-verify.cc/content/03_develop/07_checkers/
