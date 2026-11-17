# Goal 2 progress: mirror_heal.py timezone bug fix
Date: 2026-11-18
Agent: Mechanic

## What was wrong
`_last_sync_time()` in `memory/ops/mirror_heal.py` parsed log timestamps as UTC:
```python
dt = datetime.datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S").replace(
    tzinfo=datetime.timezone.utc
)
```
But `memory_mirror.log` stores LOCAL time (AEST/UTC+10 on this host). Result:
staleness check compared a future-dated timestamp against UTC now → negative age
→ always "fresh" → repair never fired.

## Fix
```python
dt_local = datetime.datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S")
dt = dt_local.astimezone().astimezone(datetime.timezone.utc)
```
Uses the system's local timezone to interpret the naive timestamp, then converts
to UTC for comparison.

## Verification
Before: `DRY-RUN: mirror fresh (-22795s < 900s) - no action` (wrong — negative age)
After:  `DRY-RUN: STALE detected (13217s > 900s), would re-run mirror` (correct)

## Remaining
- schtask registration (queued in non-sandbox-queue.md; needs non-sandbox seat)
- First live repair_ok row in mirror-repairs.jsonl after task is registered