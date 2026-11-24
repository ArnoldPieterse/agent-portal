# Autonomous Recovery Time Trend Analysis — Verifier Goal #7 (2026-11-25)

## Script: memory/verifier/recovery_trend.py

## Self-test: 6/6 PASS
- T1: stable data → no degradation alert
- T2: +66.7% spike correctly flagged (>10% threshold)
- T3: multi-type independent trends (one degrades, other doesn't)
- T4: sparse data (<3 samples) handled gracefully with note
- T5: p95 computation correct
- T6: no previous window → trend=None

## Live run: PASS
- 5 incidents found (all host_down on white)
- Recovery times correlated from portal-heal-log health_check_ok events
- Current mean: 6010.2s, p95: 6755.0s
- No degradation alert (insufficient history for previous window)

## CWD-independence: verified (runs from both repo root and memory/verifier)
