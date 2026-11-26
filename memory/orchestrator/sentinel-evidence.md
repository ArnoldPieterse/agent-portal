# Convergence Regression Sentinel - Evidence

Date: 2026-11-26
Script: memory/orchestrator/convergence_sentinel.py

## Self-test results (4/4 PASS)
- T1: 8pt drop -> exactly 1 alert + 1 remediation goal in responsible lane + idempotent re-run
- T2: accelerating series (60->65->72) -> no alert
- T3: duration_score component drop -> correctly attributed to mechanic lane
- T4: 3pt drop (below 5pt threshold) -> no alert (deceleration, not regression)

## Real run
Status: ok (cycle 24, score 71.3, climbing from 69.1 in cycle 23)
No regression detected - correct behavior.

## Design notes
- Threshold: 5.0 pts drop = regression; below that = mere deceleration
- Attribution: largest negative component delta -> mapped lane (pass_autonomy->orchestrator, duration_score->mechanic, rework_score->builder, trend_score->scribe)
- Idempotency: checks alerts.jsonl for existing convergence_regression alert on same cycle before writing
- Remediation goal format: [SENTINEL:<cycle>] marker in lane goals file for easy detection
