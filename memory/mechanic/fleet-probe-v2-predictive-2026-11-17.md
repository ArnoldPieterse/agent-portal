# Fleet Probe v2: Predictive Trend Alerts — Evidence
Date: 2026-11-17
Goal: #3 (Adaptive probe v2: predictive alerts)
Status: CODE BUILT + SIMULATED; needs production runs for full closure

## What was built
Added `predictive_trend()` to fleet_probe_v2.py:
- Simple linear regression on last 3+ OPEN latency readings per host:port
- If slope > 10% of latest value per interval -> escalates OK to WARN (PREDICTIVE_WARN)
- New field in results: `trend_pct` (null unless trending)

## Acceptance test result (simulation, 2026-11-17)
Scenario: host degrading +20%/interval from 50ms baseline
```
Interval 2: latency=72.0ms drift=+44% -> PREDICTIVE-WARN (below 50% threshold!)
Interval 3: latency=86.4ms drift=+73% -> actual WARN
Interval 7: latency=179.2ms drift=+258% -> CRIT
```
Lead time: **5 intervals** early warning before CRIT.
Unit tests: 6/6 PASS (stable, degrading, insufficient data, mixed status, subtle, clear).

## Remaining for full closure
- [ ] 3+ consecutive production runs from non-sandbox seat showing real trend detection
- [ ] One simulated degrade test on live host (or use sim_fleet_probe_degrade.py if it exists)

## Files modified
- fleet_probe_v2.py: +predictive_trend(), +TREND_MIN_POINTS, +TREND_WARN_SLOPE, integrated into run_probe()