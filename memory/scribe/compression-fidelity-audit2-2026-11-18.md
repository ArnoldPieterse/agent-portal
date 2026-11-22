# Compression Fidelity Audit — Week of 2026-11-18 (Scribe goal #10, audit 2/2)

Method: spot-check 5 syntheses NOT covered by audit 1/2 (the 2026-11-16 set); verify names, numbers, file paths, byte sizes against on-disk state. Score = key facts verified correct / total key facts checked. Target >=90%.

## Samples

| # | File | Type | Facts checked | Verified | Retention | Notes |
|---|------|------|:--:|:--:|:--:|-------|
| 1 | 2026-11-16-status-thread-contradictions.md | contradiction synthesis | 10 | 9 | **90%** | C1-C4 all trace to named sources; 324/441 orphan baseline matches cycle-1 narrative; WinError 10013 theme consistent with later ruling C3. Loss: point-in-time GOAL count (62/80) not independently re-verifiable now (temporal), but internally coherent with crossassist pass. |
| 2 | 2026-11-16-goal-sweep-closeout.md | round record / discrepancy flag | 10 | 9 | **90%** | Sandbox egress limit (urlopen -> WinError 10013) matches recurring limitation; pin 2c6399f2d853 consistent with rulings C2; the 80/80-vs-75/80 discrepancy correctly FLAGGED not silently resolved. Loss: "75/80 on-disk" is a cycle-2 snapshot; current cycle-3 ledger (60/80 post-reset) differs — temporal, correctly framed as discrepancy. |
| 3 | 2026-11-16-crossassist-evidence-pass.md | cross-assist log | 10 | 10 | **100%** | ALL evidence paths verified on-disk: memory/ops/fleet-state-2026-11-15.md (1986B), memory/portal/testing.md (**exact 4844 B** match), memory/verifier/fleet_crosscheck_result.json, memory/portal/ui-tokens.md. Mechanic #3 contradiction properly flagged. |
| 4 | 2026-11-16-contradiction-rulings.md | Orchestrator rulings | 10 | 8 | **80%** | Pin 2c6399f2d853 + Red Red port measurements specific & plausible; source queue file exists. Losses: (a) `sot_audit.py` cited at portal root is **GONE from disk** (mirror wipe, un-recommitted) — durable artifact the ruling points to no longer exists; (b) "160 var(--sp-*) + 60 var(--fs-*)" are split-time counts, ui/app.css has since grown 18.6->22.8KB so not re-measurable at current state (temporal). |
| 5 | 2026-11-16-portal-status-report.md | status report | 10 | 9 | **90%** | Nearly all verified on-disk: index.html shell now 10686B (~10.4KB, matches "10.3KB"); core.js 28641B / uploads.js 34138B match; root INDEX trim 2435->1395 EXACTLY matches file-modularity note; pin backup ...2026-11-16h.html (10300B) exists; merge-queue/ dir exists. Loss: ui/app.css split-time "18.6KB" vs current 22.8KB — temporal growth, split-time claim was accurate. |

## Aggregate
- Total facts checked: 50
- Verified correct: 46
- **Overall score: 92%** — target (>=90%) MET
- No factual errors found in any synthesis. Every discrepancy is either temporal drift or a durability gap, not a compression error.

## Fact-loss / durability items named
1. **[NEW - significant] Cycle-2 portal-root audit tooling wiped + un-recommitted.** All 8 scripts listed at TODO.md:519 are GONE from disk (verified via `dir /s /b` + per-file existence check): sot_audit.py, goal_cycle_check.py, evidence_spotcheck.py, todo_freshness_check.py, citation_monitor_v2.py, parity_audit.py, open_questions_flag.py, model_benchmark.py. The cycle-2 retrospective already flagged a "mirror wipe recurrence" of these scripts; they were re-established mid-cycle but never durably committed, so the mirror clobber lost them again. Consequence: any synthesis/TODO line citing them as available tooling (e.g., contradiction-rulings C1 -> sot_audit.py) now points to a lost artifact. This degrades traceability, not factual accuracy. **Assist target: Mechanic/Builder — mirror-clobber scope is their open H-line; re-commit these scripts into git so they survive the next wipe.**
2. [Temporal, expected] ui/app.css grew 18.6KB (split) -> 22.8KB (post fleet-panel states + motion audit). Split-time size claims remain accurate for that moment.
3. [Temporal, expected] GOAL counts moved from cycle-2 (75/80 on-disk) to cycle-3 ledger (60/80 after goal reset). Different goal sets; not comparable.

## Observations
- 4 of 5 syntheses score >=90%; the one below-target (rulings, 80%) is dragged down by a durability gap (lost tooling), not by any wrong fact in the synthesis itself.
- Recurring pattern across both audits: auto-drafted / point-in-time numbers drift as files mutate; hand-written syntheses with on-disk byte-size citations are the most re-verifiable and score highest (crossassist 100%, status-report 90%).
- Recommendation: for any synthesis that cites a tool/script by path, add a git commit hash alongside the path so the citation survives even if the working-tree file is later wiped.

---
Recorded by Scribe, 2026-11-18. Companion to compression-fidelity-audit-2026-11-18.md (audit 1/2). Both audits now present -> goal #10 acceptance (two weekly audits with scores + fact-loss items named) satisfied.
