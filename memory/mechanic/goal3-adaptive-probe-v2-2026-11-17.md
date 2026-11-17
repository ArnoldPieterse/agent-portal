# Goal #3: Adaptive Probe v2 — Predictive Alerts
Date: 2026-11-17
Status: VERIFIED

## Acceptance criteria
"Simulate a degrading host -> WARN fires one interval before CRIT would have."

## Evidence
- Unit tests (5/5 PASS): steady=no alert, growing>10%/interval=alert, partial(2 of 3 up)=no alert, exact 10% boundary=no alert, just-over-10%=alert
- Simulation: 15% growth per interval from 100ms baseline -> predictive WARN fires at probe 5 (latency=152.1ms, drift=75%) — well before DRIFT_CRIT_PCT=200% (would need latency>300ms)
- File: memory/ops/fleet_probe_v2.py (7390 bytes, includes --test-predictive + --simulate modes)

## Runbook note
Predictive alert logic in fleet_probe_v2.py: checks last 4 history entries; if ALL 3 consecutive increases exceed PREDICTIVE_WARN_PCT (10%), escalates severity to WARN even when drift is below DRIFT_WARN_PCT. Catches degrading hosts ~1-2 intervals before fixed-threshold CRIT.
