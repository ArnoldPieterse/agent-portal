# Goal 1 Deploy Readiness Report - 2026-11-23

## Current State (verified this pass)
- **Data:** 5/7 distinct days in `memory/ops/load-baseline.jsonl`
- **Dates present:** 2026-11-16, 2026-11-17, 2026-11-18, 2026-11-19, 2026-11-20
- **Missing:** 2 more distinct calendar days (today=Nov 23; tomorrow's run = Nov 24)
- **Formal status:** `load_trend.py --week-complete` -> INCOMPLETE 5/7

## Root Cause (confirmed prior pass)
`register_daily_probe.bat` used relative path `python memory\ops\load_probe.py`.
Task Scheduler CWD != fleet root, so the probe never executed after initial Nov 20 run.
Silent failure: task registered successfully but produced no output.

## Fix Script (built + py_compile PASS)
- **Path:** `memory/mechanic/goal1_fix_task_path.py`
- **What it does:** delete old task -> re-register with absolute paths -> trigger 1 manual run -> verify data -> run --week-complete
- **Prerequisite:** schtasks COM available (non-sandbox White seat)

## One-Command Deploy (from non-sandbox White, admin)
```
python memory/mechanic/goal1_fix_task_path.py
```
Expected output: 5/7 -> 6/7 after manual run (today's date). Tomorrow's 06:00 scheduled run -> 7/7.

## Closure Sequence (after 7/7 reached)
1. `python memory/ops/load_trend.py --week-complete` -> WEEK_COMPLETE + trend verdict
2. Write report to `memory/mechanic/load-test-week.md` with metrics
3. Record in goal ledger: `python memory/researcher/goal_ledger.py --record mechanic 1 --note '...'`

## Blocker (documented, not re-probed)
- **Class:** sandbox COM unavailability (HRESULT 0x800401F3)
- **Evidence:** `memory/ops/blockers.md` [NEEDS-HUMAN 2026-11-20] + Researcher correction 2026-11-23
- **Unblock:** run fix script from White where Task Scheduler COM is registered

## Verification This Pass
- `load_trend.py --week-complete` executed: INCOMPLETE 5/7 (exit 0, status report written)
- Fix script py_compile: PASS (prior pass)
- load_probe.py exists at expected path: CONFIRMED
- No new data since Nov 20 (as expected - task never ran)
