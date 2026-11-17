# Goal #4 - --week-complete flag restored + validated (2026-11-17 ~17:44)

## Problem
Mirror revert lost the `--week-complete` flag from load_trend.py (3rd revert cycle).

## Fix
Re-added `--week-complete` and `--baseline-file` args to load_trend.py. 
- `--week-complete`: requires >= 7 days, produces memory/ops/load-week-report.json with per-concurrency min/max/mean for p50/p95/p99 + total errors + PASS/FAIL verdict.
- `--baseline-file PATH`: override for testing without touching real data.

## Verification (3 tests)
1. `python memory/ops/load_trend.py --week-complete` → exit 1, "only 2/7 days collected - not yet ready" ✓
2. `python memory/ops/load_trend.py --week-complete --baseline-file memory/ops/load-baseline-test-7day.jsonl` → exit 0, "7 days, 0 errors -> PASS" ✓ (report at memory/ops/load-week-report.json)
3. `python memory/ops/load_trend.py` → "load_trend OK (2 days, no regression > 30%)" ✓ (normal mode unchanged)

## Remaining dependency
Days 3-7 of REAL data require White schtask `PortalLoadProbe` to run daily at 06:00. 
Once 7 real days exist, single command closes the goal:
```
python memory/ops/load_trend.py --week-complete
```

## Runbook note
Mirror reverts load_trend.py; if --week-complete disappears again, restore from this evidence file.
