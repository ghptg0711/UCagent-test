---
name: submission-review-and-grading
description: Reviews the NutShell Cache verification submission against the contest grading rubric (100-point scale, 4 weighted dimensions, first-prize threshold 85) before final delivery. Invoke before each final submission, when user asks for a review/grade, or to generate the review report and follow-up revision plan.
---

# Submission Review & Grading (最终提交评审)

This skill is the mandatory gate before any "final submission" version. It grades the project against the official contest rubric, emits a review report, and produces a prioritized revision plan. **Every final-submission candidate must pass through this skill.**

## When to Invoke

- About to tag/release a final submission version
- User asks "评审一下" / "打分" / "能拿几等奖" / "review before submit"
- Need to produce `docs/submission_review_report.md`
- Need a gap list against the first-prize (85-100) bar
- After any major change, re-grade to confirm no regression in score

## Official Grading Rubric (must apply verbatim)

### Four Evaluation Dimensions (weight)

| Dimension | Indicator | Weight |
| --- | --- | --- |
| 完备性 (Completeness) | Env covers core read/write/miss-replace paths; run stability | 40% |
| 技术深度 (Technical Depth) | Toffee usage rationality; complex-logic fault detection; CRV randomization degree | 30% |
| AI 使用效能 (AI Efficacy) | UCAgent's role in coding efficiency & fault localization; Prompt strategy innovation | 20% |
| 工程质量 (Engineering Quality) | Repo structure, doc clarity, report data support | 10% |

### Quantified "Human Collaboration" Score (100 points)

**维度一:验证实操深度 (60 分)**

| Sub-item | Points | Key criterion |
| --- | --- | --- |
| 基础环境构建 | 20 | Picker/Toffee runnable closed loop |
| 人工干预与优化 [core weight] | 25 | Manual perf opt / logic fix / feature extension on top of UCAgent output; hand-written advanced components for replacement & coherence |
| 验证覆盖率达标 | 15 | Real run completeness; pure AI rarely reaches >90% functional coverage — this is where manual validation value shows |

**维度二:验证报告与协同分析 (40 分)**

| Sub-item | Points | Key criterion |
| --- | --- | --- |
| 协同过程记录 [new focus] | 20 | Detailed record: which modules AI generated? what errors/blind spots human found in AI code? how human fixed via Prompt Tuning or direct rewrite |
| 工程规范与可复现性 | 20 | Industrial-grade repo norm |

### Award Tiers

| Tier | Score | Persona |
| --- | --- | --- |
| 一等奖 | 85-100 | 资深验证专家视角: high human-logic density, not AI堆砌; detailed "AI缺陷与人工修正对比表"; developer leads strategy & bug interception |
| 二等奖/参与奖 | 60-84 | 合格工程师视角: core功能验证完成, basic人工校验, 仿真结果真实有效 |

### 一票否决 (Veto — any failure = disqualified)

| Veto item | Check |
| --- | --- |
| 开源合规性 | Root `LICENSE` is standard Apache 2.0 |
| 工程规范性 | Conventional `src/ tests/ docs/` layout; no meaningless redundant intermediates |
| 严禁"纯AI刷票" | Code is NOT raw UCAgent output; has manual logic injection; can handle complex scenarios; no unfixed obvious AI logic fallacies |

## Review Procedure

1. **Veto check first** — fail any veto → stop, report, do not score.
2. **Collect evidence** per sub-item (files, commands, reports).
3. **Score each sub-item** with evidence citation and a deduction reason.
4. **Sum to total**, map to tier.
5. **Generate `docs/submission_review_report.md`** from the template below.
6. **Produce revision plan** prioritized by score impact (P0 > P1 > P2).
7. **Re-run after fixes** until target tier is stably reached.

## Scoring Rubric (project-specific calibration)

### 维度一.1 基础环境构建 (20)
- Picker Python DUT builds + `tests/test_real_dut_smoke.py` PASS → 8
- Toffee adapter drives clock/reset/req, samples resp, memory agent fill+writeback → 8
- Closed loop: generator→adapter→scoreboard→coverage end-to-end on real DUT → 4
- Deduct if: only mock DUT, no real DUT smoke; adapter has hardcoded signals; no memory agent.

### 维度一.2 人工干预与优化 (25) [core]
- Parameterized policies (LRU/FIFO/Random, write-allocate/no-write-allocate) hand-verified → 6
- OOO scoreboard (txn_id match, orphan/duplicate detection) → 4
- ≥5 fault types incl. tag/error, all detected → 4
- ≥2 RTL design bugs found & evidenced (BUG-010/011 style) → 6
- Hand-authored corner-case directed sequences beyond UCAgent reach → 5
- Deduct if: policies only default; in-order only; <5 faults; no RTL bug; directed cases are trivial AI output.

### 维度一.3 覆盖率达标 (15)
- Functional coverage ≥90% on combined suite → 10; 100% → 15
- Real DUT functional coverage measured (not just core) → bonus evidence
- Deduct if: only single seed; coverage relies entirely on directed without CRV; no convergence data.

### 维度二.1 协同过程记录 (20) [focus]
- `reports/ai_collaboration_log.md` has per-round AI-generated vs manual-modified records → 6
- `reports/bug_tracker.md` records AI blind spots (e.g. BUG-002/004/005/009 are AI-code defects) → 6
- **"AI缺陷与人工修正对比表"** explicitly present → 5 (first-prize requirement)
- Prompt Tuning strategy documented → 3
- Deduct if: log is narrative only without the comparison table; no Prompt strategy.

### 维度二.2 工程规范与可复现性 (20)
- `src/ tests/ docs/ reports/ configs/ scripts/` conventional layout → 5
- WSL2 reproducible commands documented & CI green → 5
- Verilator coverage + VCD waveform artifacts → 4
- Dockerfile + health check → 3
- No redundant intermediates committed → 3
- Deduct if: .so/.vcd committed without .gitignore discipline; missing LICENSE; broken CI.

## Review Report Template

Generate at `docs/submission_review_report.md`:

```markdown
# NutShell Cache 提交评审报告 (v<version>)

**评审日期**: <date>
**评审依据**: 赛题四维度评分标准 + 量化人工协同100分制
**目标等级**: 一等奖 (85-100)

## 一、一票否决检查
| 否决项 | 状态 | 证据 |
| --- | --- | --- |
| Apache 2.0 LICENSE | ✅/❌ | LICENSE:1 |
| 工程目录规范 | ✅/❌ | src/tests/docs/... |
| 纯AI刷票排查 | ✅/❌ | bug_tracker + ai_collaboration_log 人工修正记录 |

## 二、维度一:验证实操深度 (60)
| 子项 | 满分 | 得分 | 证据 | 扣分原因 |
| --- | --- | --- | --- | --- |
| 基础环境构建 | 20 | ? | ... | ... |
| 人工干预与优化 | 25 | ? | ... | ... |
| 覆盖率达标 | 15 | ? | ... | ... |
| **小计** | 60 | ? | | |

## 三、维度二:验证报告与协同分析 (40)
| 子项 | 满分 | 得分 | 证据 | 扣分原因 |
| --- | --- | --- | --- | --- |
| 协同过程记录 | 20 | ? | ... | ... |
| 工程规范与可复现性 | 20 | ? | ... | ... |
| **小计** | 40 | ? | | |

## 四、总分与等级
- **总分: ?/100**
- **判定等级: 一等奖 / 二等奖**
- **距一等奖门槛(85)差值: ?**

## 五、AI缺陷与人工修正对比表 (一等奖必备)
| 模块 | AI生成内容 | AI缺陷/盲区 | 人工修正 | 证据 |
| --- | --- | --- | --- | --- |
| ... | ... | ... | ... | BUG-xxx |

## 六、后续修改意见 (按优先级)
### P0 (阻断一等奖,必须修)
- ...

### P1 (提升得分)
- ...

### P2 (锦上添花)
- ...
```

## Revision Plan Priority Rules

- **P0**: items that drop total below 85, or risk a veto; fix first.
- **P1**: items worth ≥3 points with low effort; clear wins.
- **P2**: polish items (<3 points or high effort); do only after P0/P1.
- Each P-item must state: what to change, which file, expected score delta.

## Hand-off

After the report is generated, the user decides which P-items to execute. Fixes route to the relevant sub-skill (`cache-crv-designer`, `scoreboard-engineering`, `llm-check-refinement`, etc.). After fixes, re-invoke this skill to re-grade and confirm the tier is stable.
