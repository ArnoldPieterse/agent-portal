# Goal #4 Regression Demo - Self-Test Evidence (2026-11-17)

## What ran
load_trend.py analysis logic executed against synthetic 4-day baseline
(3 stable days at p95=3500ms c=200 + 1 injected day at p95=5250ms = +50%).

## Result
- c=10: ratio 1.000, no regression (correct)
- c=50: ratio 1.000, no regression (correct)
- c=200: ratio 1.500, REGRESSION FLAGGED (correct - >30% threshold)

## Live baseline status
- 2 real days collected: Nov 16 18:37 + Nov 17 14:27
- load-trend-report.json: status=OK (improving trend, all ratios < 1.0)
- Daily schtask NOT yet registered (sandbox cannot create tasks; needs one-time elevated run)

## Remaining for goal closure
- 5 more days of real data (Nov 18-22) via daily schtask PortalLoadProbe
- One real regression event caught in production (or documented synthetic demo = this file)

## Pipeline components verified working
1. load_probe.py - concurrent GETs at 10/50/200, p50/p95/p99 [PASS]
2. load_trend.py - rolling median comparison, >30% threshold flag [PASS]
3. Outage guard - all-error levels excluded from baseline [PASS]
4. Report output - memory/ops/load-trend-report.json [PASS]

## Schtask command (run once elevated)
schtasks /create /tn PortalLoadProbe /tr "python C:\Users\Red\Documents\agent-folder\memory\ops\load_probe.py" /sc daily /st 06:00 /f
