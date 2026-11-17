# Goal #4 (cycle-3 #1) - --week-complete restored 5th time 2026-11-17

## What broke
Mirror LWW pull reverted load_trend.py again (5th observed revert), removing `--week-complete` and `--baseline-file` args.

## Fix
Re-applied both flags + week_complete() function to memory/ops/load_trend.py.

## Verification (3 tests, all pass)
1. `python memory/ops/load_trend.py` → "load_trend OK (2 days, no regression > 30%)" ✓
2. `python memory/ops/load_trend.py --week-complete` → exit 1, "only 2/7 days collected - not yet ready" ✓
3. `python memory/ops/load_trend.py --week-complete --baseline-file memory/ops/load-baseline-test-7day.jsonl` → exit 0, "7 days, 0 errors -> PASS" ✓

## State
- Real baseline: 2/7 days (Nov 16 + Nov 17)
- Remaining dependency: White schtask `PortalLoadProbe` daily at 06:00 for 5 more days
- Closure command (when 7 days exist): `python memory/ops/load_trend.py --week-complete`
- Expected closure date: ~2026-11-22

## Runbook note
Mirror reverts load_trend.py every cycle. If --week-complete disappears, restore from this file. The function is self-contained (week_complete + 2 argparse lines).