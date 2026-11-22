# Goal 1 - Closure Logic Meta-Test (2026-11-23)

## Purpose
Verify that `load_trend.py --week-complete` produces correct verdicts for all paths,
de-risking the closure sequence when real 7/7 data arrives from White.

## Tests Executed (this pass, sandbox-safe - no network/GPU/schtasks needed)

### Test 1: WEEK_COMPLETE happy path
- Input: 7 distinct days of synthetic latency data (c=10/50/200)
- Expected: status=WEEK_COMPLETE, trend_status=OK
- **Result: PASS** - correct verdict, no false regressions

### Test 2: INCOMPLETE path
- Input: 5 distinct days (Nov 16-20, matching current real data)
- Expected: status=INCOMPLETE, days_present=5, missing_count=2
- **Result: PASS** - correctly reports gap

### Test 3: REGRESSION_DETECTED path
- Input: 7 days where last day has p95 +75% vs median
- Expected: status=WEEK_COMPLETE, trend_status=REGRESSION_DETECTED
- **Result: PASS** - regression correctly flagged at c=10

### Test 4: Outage guard (all_errors exclusion)
- Input: 6 valid days + 1 all_errors row (portal down)
- Expected: all_errors row excluded from day count -> INCOMPLETE 6/7
- **Result: PASS** - outage guard correctly prevents data poisoning

## Current Real Data State
- `memory/ops/load-baseline.jsonl`: 9 valid latency rows across 5 distinct days
- Dates: 2026-11-16 through 2026-11-20
- `load_trend.py --week-complete` output: INCOMPLETE 5/7

## Conclusion
Closure logic is verified. When the fix script runs from White and accumulates
2 more days of real data, `--week-complete` will produce the correct verdict.
No code changes needed - the path is clear.

## One-Command Deploy (from non-sandbox White)
```
python memory/mechanic/goal1_fix_task_path.py
```
Expected: 5/7 -> 6/7 immediately; 7/7 after next day's scheduled 06:00 run.
