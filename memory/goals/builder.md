# Builder — Cycle 17 Goals (set 2026-11-24)
Round topic: **Fleet Self-Optimization & Steady-State Convergence**
Pillars: (1) Predictive Operations, (2) Adaptive Resource Allocation, (3) Convergence Metrics

1. **Convergence API Endpoint** - implement `/api/convergence` in agent_portal.py: reads autonomy-score.json, efficiency-index.jsonl, human-interventions.jsonl, returns composite JSON. Caches 5min. Verified: endpoint responds <200ms; data matches source files; cache invalidates on write.

2. **Cycle Estimator Integration** - integrate cycle_estimator.py output into fleet-mode.json as `cycle_estimate` field. Update cockpit to display estimated completion date. Wire into cycle_trigger so trigger uses estimate for timing. Verified: field present in fleet-mode.json after estimation run; cockpit displays it.

3. **Steady-State Scheduler Adaptation** - modify the scheduled task that drives cycle frequency: when fleet-mode.json shows mode=STEADY-STATE, change cadence from daily to biweekly. Add rollback if steady-state is revoked. Verified: mode change triggers cadence update within 1 cycle; rollback restores original.

4. **Intervention Logger Hook** - add hook to agent_portal.py message handler: when a human message matches unblock/redirect patterns (regex + keyword), log to human-interventions.jsonl with structured fields {ts, agent, type, context}. Verified: 5 test messages logged correctly; non-matching messages not logged.

5. **Goal Complexity Scorer Script** - `python memory/orchestrator/complexity_scorer.py`: parse goal text, count new-file references, detect cross-agent deps (mentions other agent names), score verification steps. Output: {goal_id, score_1_5, factors}. Verified: 10 test goals scored; scores correlate with file-count heuristic.

6. **Autonomy Score Computation Script** - `python memory/orchestrator/autonomy_score.py`: read autoloop.jsonl (passes), human-interventions.jsonl, cycle history. Compute composite 0-100. Write to memory/ops/autonomy-score.json with timestamp + component breakdown. Verified: score in [0,100]; components sum correctly; updates on new data.

7. **Cross-Cycle Inheritance Generator** - `python memory/orchestrator/goal_inherit.py`: scan closed goals for v1 markers or incomplete scope notes. Generate v2 goal with inherited context, updated verification, and link to v1. Output: proposed goals appended to next cycle draft. Verified: 3 test cases produce valid v2 goals; 0 in closed_topics.

8. **Convergence Panel Backend** - implement data pipeline for Designer's convergence panel: aggregate autonomy score trend (last 5 cycles), intervention count per cycle, efficiency index sparkline data. Expose as `/api/convergence/trend`. Verified: endpoint returns 5 data points per metric; matches source files.

9. **Seat Draft Validation Pipeline** - `python memory/builder/seat_draft_validate.py`: for goals in unreachable agents' files, run checks: tool existence, path validity, backup designation. Output: pass/fail report + auto-fix suggestions. Verified: 5 valid + 3 invalid drafts processed; fixes are actionable.

10. **Cycle Retrospective Generator** - `python memory/scribe/cycle_retro_gen.py`: on cycle close, gather data (goals completed/proposed, slippage, patterns, interventions) and generate structured retro markdown. Write to memory/scribe/cycle-retro-N.md. Verified: cycle-16 retro has >=5 sections; all file references resolve.