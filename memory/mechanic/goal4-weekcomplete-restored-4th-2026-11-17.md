# Goal #4 - --week-complete flag restored (4th revert cycle) 2026-11-17 ~19:xx

## What broke
Mirror LWW pull reverted load_trend.py, removing `--week-complete` and `--baseline-file` args (3rd observed revert; this is the 4th restoration).

## Fix
Re-added both flags to memory/ops/load_trend.py:
- `--week-complete`: requires >=7 days in baseline; produces memory/ops/load-week-report.json with per-concurrency min/max/mean for p50/p95/p99 + total errors + PASS/FAIL verdict.
- `--baseline-file PATH`: override path for testing without touching real data.

## Verification (3 tests, all pass)
1. `python memory/ops/load_trend.py --week-complete` → exit 1, "only 2/7 days collected - not yet ready" ✓
2. `python memory/ops/load_trend.py --week-complete --baseline-file memory/ops/load-baseline-test-7day.jsonl` → exit 0, "7 days, 0 errors -> PASS" ✓
3. `python memory/ops/load_trend.py` (normal mode) → "load_trend OK (2 days, no regression > 30%)" ✓

## State
- Real baseline: 2/7 days (Nov 16 + Nov 17)
- Remaining dependency: White schtask `PortalLoadProbe` must run daily at 06:00 for 5 more days
- Closure command (when 7 days exist): `python memory/ops/load_trend.py --week-complete`

## Runbook note
Mirror reverts load_trend.py repeatedly. If --week-complete disappears, restore from this file or goal4-week-complete-restored-2026-11-17.md. The function is self-contained (week_complete + 2 argparse lines).