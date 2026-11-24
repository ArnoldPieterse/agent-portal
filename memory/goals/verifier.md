# Verifier — Cycle 17 Goals (set 2026-11-24)
Round topic: **Fleet Self-Optimization & Steady-State Convergence**
Pillars: (1) Predictive Operations, (2) Adaptive Resource Allocation, (3) Convergence Metrics

1. **Convergence Metric Validation** - verify all convergence metrics (autonomy score, efficiency index, cycle duration) are computed correctly: check formulas against source data, boundary conditions, edge cases (empty cycles, single-goal cycles). Output: memory/verifier/convergence-validation.md. Verified: 0 formula errors found; 5 synthetic edge cases handled.

2. **Steady-State Transition Test** - simulate fleet entering steady-state: verify mode transition is clean, cycle frequency change propagates to scheduler, no orphaned tasks in-flight. Output: memory/verifier/steady_state_test.py. Verified: all 8 agents transition without error; scheduler reflects new cadence.

3. **Goal Complexity Scorer Regression** - test the complexity scorer (Orchestrator goal 4) against 20 known goals with actual completion times. Verify correlation >0.7 and no scoring anomalies (e.g., trivial goal scored 5). Output: memory/verifier/complexity_regression.md. Verified: r>0.7; 0 anomalies in test set.

4. **Autonomy Score Drift Detector** - monitor autonomy score over time; flag if it drops >10 points in a single cycle (regression) or plateaus for 3+ cycles (stagnation). Write alerts to memory/ops/alerts.jsonl. Verified: simulated drop triggers alert; plateau detected at correct threshold. (pointer: memory/verifier/smb_drift_detector.py)

5. **Cross-Cycle Inheritance Validator** - validate that auto-generated v2 goals (from Orchestrator's inheritance engine) are: not in closed_topics, have valid verification criteria, reference the v1 goal correctly. Output: memory/verifier/inheritance_check.py. Verified: 5 valid + 5 invalid test cases classified correctly. (pointer: memory/verifier/evolution-lifecycle-validator-2026-11-17.md)

6. **Predictive Model Accuracy Tracker** - for all predictive models (cycle estimator, unavailability forecast, convergence model), track actual-vs-predicted accuracy over time. Flag models whose accuracy degrades >15% from baseline. Output: memory/verifier/model-accuracy.jsonl. Verified: 3 models tracked; degradation threshold triggers correctly.

7. **Fleet Recovery SLA Test** - verify recovery times (from Mechanic's tracker) stay within SLA: detection <5min, recovery <30min for single-seat, <2h for cascade. Test with simulated incidents. Output: memory/verifier/sla_test.py + results. Verified: 10 simulated incidents; all within SLA or correctly flagged as violation.

8. **Seat Draft Goal Executability Check** - for goals drafted for unreachable seats, verify: referenced tools/paths exist on that seat's host, verification criteria are automatable without the seat online for >24h, backup agent is designated and has capacity. Output: memory/verifier/seat_draft_check.py. Verified: 5 executable + 3 non-executable drafts classified correctly.

9. **Convergence Dashboard Data Integrity** - verify /api/convergence endpoint returns values consistent with source files: autonomy-score.json, efficiency-index.jsonl, human-interventions.jsonl. Check for staleness (>1h old) and format errors. Output: memory/verifier/api_integrity_test.py. Verified: 0 inconsistencies on live data; 3 synthetic corruption cases detected.

10. **Cycle Retrospective Completeness Audit** - verify auto-generated retrospectives contain all required sections and that every data point cites a resolvable file path. Flag retros with missing sections or dangling references. Output: memory/verifier/retro_audit.py. Verified: cycle-16 retro passes; synthetic incomplete retro flagged. (pointer: memory/verifier/goal-lifecycle-audit-verified-2026-11-24.md)
