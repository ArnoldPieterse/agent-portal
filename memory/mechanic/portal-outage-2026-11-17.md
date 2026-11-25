# Portal Outage - 2026-11-17 2026-11-17 11:56:31

## Finding
Portal (:8099) was DOWN at probe time (11:55). Load probe recorded 50/50 errors at all concurrency levels.

## Recovery Attempt
- `python agent_portal.py` from sandbox fails: PermissionError on C:\Users in `_find_sandbox_dir()`
- Workaround: set USERPROFILE=C:\Users\<red> -> process starts but does NOT bind port 8099 within 8s
- Root cause of non-bind: likely SMB sync initialization blocking before HTTP server starts; sandbox lacks proper COM/network access

## Resolution Needed
Host-level watchdog (PortalWatchdog schtask, 5-min cadence) should auto-restart. If it is not firing, check:
1. `schtasks /query /TN PortalWatchdog` - is the task registered?
2. COM availability on host (known broken in sandbox per 2026-11-17 note)

## Data Point
load-baseline.jsonl now has 2 entries: day-1 healthy (Nov 16, 0 errors) + day-2 outage (Nov 17, 50/50 errors).
