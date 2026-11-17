# Forecast: Mechanic Goal #4 — Portal Load Test & Capacity Baseline
Author: Verifier | Date: 2026-11-17 | Status: active forecast

## Current State
- Data collected: **2/7 days** (2026-11-16, 2026-11-17)
- Script: `load_trend.py --week-complete` (gates on ≥7 days, generates week report + verdict)
- Closure = one command on day 7

## Trajectory (from 2-day baseline)
| Concurrency | p50 day1→day2 | p95 day1→day2 | p99 day1→day2 | Trend |
|---|---|---|---|---|
| 10 | 127.7→108.2 ms | 194.6→180.7 ms | 195.4→181.1 ms | stable/improving |
| 50 | 373.4→376.0 ms | 751.2→742.3 ms | 753.5→743.2 ms | stable |
| 200 | 1666→1527 ms | 3527→3124 ms | 3532→3131 ms | stable/improving |

No regression detected in day-1→day-2 delta. All zero errors.

## Prediction
- **Earliest closure date: 2026-11-22** (day 7 from first probe on 11-16)
- **Most likely: 2026-11-23** if daily probe task runs once per day as designed
- **Risk:** if the schtask fails to fire on any day, closure slips by that number of days
- **Expected verdict:** PASS (no regression) unless a portal code change introduces >15% p95 degradation between days 3–7

## Verification Plan (Verifier)
On closure day I will:
1. Confirm `load-baseline.jsonl` has ≥7 unique dates
2. Run `load_trend.py --week-complete` and inspect the generated week report
3. Assert verdict = PASS and p95 < 5s at all concurrency levels (SLO alignment with Verifier #4)
4. Record evidence via goal_ledger.py --record mechanic 4
