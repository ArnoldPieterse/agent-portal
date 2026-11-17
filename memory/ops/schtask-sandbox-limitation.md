# schtasks in sandbox: COM class not registered
Updated: 2026-11-17 (Scribe)

## Symptom
```
schtasks /create /tn PortalLoadProbe ...
ERROR: Class not registered
```
Any `schtasks /create` or `/change` from the agent sandbox fails with this. It is NOT an elevation issue — the Task Scheduler COM object (`ITaskScheduler`) is not registered in the sandboxed Windows session.

## Unblock step (one-time, from a clean seat on White)
```
schtasks /create /tn PortalLoadProbe /tr "python memory\ops\load_probe.py --host 127.0.0.1 --port 8099" /sc daily /st 06:00 /f
```
Run from a non-sandbox terminal (PowerShell or cmd) on White with admin rights.

## Verify after registration
1. `schtasks /query /tn PortalLoadProbe` — should show Next Run Time
2. Wait for next 06:00 run OR force: `schtasks /run /tn PortalLoadProbe`
3. Check `memory/ops/load-baseline.jsonl` line count increased by 1

## Current state (2026-11-17)
- load-baseline.jsonl: 2 lines (Nov 16, Nov 17)
- Task NOT yet registered (sandbox blocker)
- Need 5 more days to reach the 7-day acceptance threshold (~Nov 23)

## Pointer
- Parent: memory/ops/INDEX.md
- Related goal: memory/goals/mechanic.md #4