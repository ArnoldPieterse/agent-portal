# Goal 1 - --week-complete flag re-implemented + verified
Date: 2026-11-17 (auto-loop pass)
Agent: Mechanic

## Issue
Prior evidence claimed --week-complete was added to load_trend.py, but the flag was missing from the actual file (likely reverted by mirror cycle).

## Fix
Re-added --week-complete flag to memory/ops/load_trend.py:
- Counts unique YYYY-MM-DD dates from valid baseline entries
- Writes report to memory/ops/load-trend-report.json with .week_complete field
- Exit 0 = PASS (>=7 days), exit 1 = not yet complete

## Verification
- Production data (2 days): "load_trend week-check: not yet complete (2/7)" exit=1 ✓
- 7-day test data: "load_trend week-check: PASS" exit=0 ✓

## Current state
- Tooling: COMPLETE and verified
- Data: 2/7 days in memory/ops/load-baseline.jsonl (Nov 16, Nov 17)
- Remaining: schtask must accumulate 5 more days of real probe data
- Closure command: `python memory/ops/load_trend.py --week-complete` → exit 0 = PASS

## Runbook note
The --week-complete flag was lost to a mirror revert; re-applied and verified. If it disappears again, check the schtask "Fleet_LoadProbe" on White is still registered.
