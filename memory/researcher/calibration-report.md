# Prediction Calibration Report
Generated: 2026-11-22T23:46:05Z

## Summary
- Predictions available: **10**
- Matched to actuals: **10**
- Unmatched (no corresponding goal in ledger): **0**
- **Brier score: 0.4575** (0=perfect, 1=random)
- Mean predicted probability: 0.362
- Mean actual outcome: 1.000
- **Calibration: UNDER-confident (predictions too low)**

## Reliability Table
| Bin | Count | Mean Predicted | Mean Actual | Gap (Actual-Predicted) |
|-----|-------|---------------|-------------|------------------------|
| [0.0, 0.2) | 3 | 0.043 | 1.000 | +0.957 |
| [0.2, 0.4) | 1 | 0.278 | 1.000 | +0.722 |
| [0.4, 0.6) | 5 | 0.515 | 1.000 | +0.485 |
| [0.6, 0.8) | 1 | 0.639 | 1.000 | +0.361 |

## Matched Predictions Detail
- [CORRECT] builder / Runbook Parser + Executor: P=0.52, actual=reached
- [CORRECT] mechanic / Fleet State Collector Daemon: P=0.52, actual=reached
- [MISSED] designer / Cockpit Layout Design: P=0.05, actual=reached
- [MISSED] archivist / Knowledge Index Builder: P=0.28, actual=reached
- [CORRECT] mechanic / Model OOM Auto-Recovery: P=0.52, actual=reached
- [MISSED] designer / Health Score Visualization: P=0.05, actual=reached
- [CORRECT] archivist / Citation Integrity Monitor: P=0.64, actual=reached
- [CORRECT] mechanic / Scheduled Maintenance Window: P=0.52, actual=reached
- [CORRECT] mechanic / Host Capacity Arbitration: P=0.52, actual=reached
- [MISSED] designer / Decision Timeline UX: P=0.04, actual=reached
