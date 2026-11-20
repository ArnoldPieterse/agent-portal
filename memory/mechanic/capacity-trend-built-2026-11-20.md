# Goal #9: Capacity Trend Engine Built — 2026-11-20

## What was done
Built `memory/mechanic/capacity_trend.py` (9583 B) — linear-trend prediction module for fleet resource exhaustion.

## Features
- `--append --host X --metric Y --value Z`: append a data point to `capacity_data.jsonl`
- `--report [--threshold N]`: generate prediction report with per-host/metric trend + days-to-breach
- `--selftest`: 5 synthetic tests (linear growth, stable, breached, declining, insufficient data)

## Self-test results: 5/5 PASS
- T1: slope=4/day correctly computed, r²>0.99, prediction 1.0 day to threshold
- T2: flat line → None (no prediction)
- T3: already above threshold → 0 (immediate breach)
- T4: declining → None
- T5: single point → None

## Data seeded
- White disk_pct = 44.4% (from capacity-report-2026-11-20.md, 2026-11-20T23:39)
- Need ≥2 points per metric for trend; next append will enable prediction.

## Remaining for closure
- Register daily data-collection schtask (blocked by COM/schtasks wall — same as Goal 5)
- Accumulate 7 days of data across hosts
- Validate prediction accuracy against historical data

## Runbook note
`python memory/mechanic/capacity_trend.py --append --host White --metric disk_pct --value <pct>` daily.
When schtasks COM is available, register as `CapacityTrendCollect` /sc daily.
