# Goal #1 (cycle-3) - --week-complete restored 6th time 2026-11-17

## What broke
Mirror LWW pull reverted load_trend.py again (6th observed revert), removing `--week-complete` and `--baseline-file` args.

## Fix
Re-applied both flags + week_complete() + load_days_from() to memory/ops/load_trend.py.

## Verification (3 tests, all pass)
1. `python memory/ops/load_trend.py` -> "load_trend OK (2 days, no regression > 30%)" PASS
2. `python memory/ops/load_trend.py --week-complete` -> exit 1, "only 2/7 days collected - not yet ready" PASS
3. `python memory/ops/load_trend.py --week-complete --baseline-file memory/mechanic/load_trend_test/load-baseline-7day.jsonl` -> exit 0, "7 days, 0 errors -> PASS" PASS

## State unchanged
- Real baseline: 2/7 days (Nov 16 + Nov 17)
- Expected closure date: ~2026-11-22
- Blocker already logged in memory/ops/blockers.md (NEEDS-HUMAN entry for White schtask registration)

## Runbook note
This is the 6th revert. The mirror pull LWW logic does not protect load_trend.py. Long-term fix: add load_trend.py to a protected-files list or pin it like index.html. Interim: re-apply from this file whenever --week-complete disappears.