# Goal 1 Root Cause: PortalLoadProbe Silent Failure (2026-11-23)

## Finding
PortalLoadProbe schtask was verified registered on White on 2026-11-22, but `load-baseline.jsonl`
mtime is **2026-11-20 09:00:03** — no data written in 3 days despite daily 06:00 schedule.

## Root Cause
`register_daily_probe.bat` uses a **relative path**: `python memory\ops\load_probe.py --host 127.0.0.1 --port 8099`
Task Scheduler does not inherit the caller's CWD; the relative path fails to resolve, causing
a silent exit (no data appended, no outage logged because the Python process never starts).

## Fix
`memory/mechanic/goal1_fix_task_path.py` — one-shot script that:
1. Queries current task state
2. Deletes + re-registers with **absolute paths** for both Python exe and load_probe.py
3. Triggers a manual run
4. Verifies new data appears in baseline
5. Runs `load_trend.py --week-complete` for closure status

## Current Data Status
- 5/7 unique latency dates: 2026-11-16, 17, 18, 19, 20
- Missing: Nov 21, 22, 23 (3 days)
- Once task is fixed and runs daily, closure reachable in ~2 more days (need 7 distinct dates)

## Unblock (one command from non-sandbox White with schtasks COM available):
```
python memory/mechanic/goal1_fix_task_path.py
```

## Evidence chain
- File mtime: `load-baseline.jsonl` last modified 2026-11-20 09:00:03 (confirmed this pass)
- `load_trend.py --week-complete` output: `INCOMPLETE 5/7 days`
- Registration script inspected: relative path confirmed
- Fix script: py_compile PASS
