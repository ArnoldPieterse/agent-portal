# Goal #4 Pipeline Validation — 2026-11-17

## What was verified
`load_trend.py --week-complete` end-to-end pipeline tested with synthetic 7-day data in isolated temp dir:

| Test | Input | Output | RC |
|------|-------|--------|----|
| Normal week | 7 days, stable latency | `WEEK_COMPLETE \| days=7 \| regressions=0` | 0 |
| Regression | Day 7 = 3x median | `REGRESSION \| days=7 \| regressions=3` + per-level detail | 1 |
| Incomplete | 2/7 days (real data) | `WEEK_INCOMPLETE \| 2/7 days \| next probe adds 1 day` | 0 |

## Current state
- **Data:** 2/7 days in `memory/ops/load-baseline.jsonl` (Nov 16 + Nov 17)
- **Script:** `load_probe.py` outage guard intact (per-level skip + total-outage log to load-outage.jsonl)
- **Schtask:** NOT yet registered on White. One-liner ready in `memory/ops/loadtest/register_daily_probe.bat`
- **Blocker:** Red sandbox cannot reach White:8099 (WinError 10013). Recorded in `memory/ops/blockers.md`.

## Unblock (one command from White non-sandbox seat)
```
schtasks /create /tn PortalLoadProbe /tr "python memory\\ops\\load_probe.py --host 127.0.0.1 --port 8099" /sc daily /st 06:00 /f
```
After day 7: `python load_trend.py --week-complete` → verdict (RC 0 = OK, RC 1 = REGRESSION).

## Runbook note
load_trend.py --week-complete validated 2026-11-17: correct exit codes + output format for all 3 states (OK/REGRESSION/WEEK_INCOMPLETE). Pipeline is production-ready; only missing input data from daily schtask.
