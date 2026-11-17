# Goal #8 - Chaos Drill Bug Fix (2026-11-18 auto-loop pass)

## Bug found and fixed
`kill_portal_on()` in `memory/ops/chaos_drill.py` returned `True` (success) for ALL non-Red hosts without actually killing anything. This would cause **false PASS** results during the real drill: the script would report "portal killed, recovered in 0s" when it never killed the portal at all.

## Fix applied
Rewrote `kill_portal_on()` with proper local/remote detection:
- **Local** (target IP = this host): uses `netstat -ano` to find PID on :8099, then `taskkill /F /PID <pid>`
- **Remote**: uses `elev.py --shell "powershell ..."` to run `Invoke-Command` with `Stop-Process` on the target host
- Returns `False` (honest failure) if elev.py is missing or the remote command fails

## Verification
- `test_chaos_drill_sim.py`: 14/14 PASS (unchanged, sim tests monkey-patch kill_portal_on)
- Code review: no path where a non-local target can produce a false True return

## Remaining for goal #8 closure
1. Execute on White: `python memory/ops/register_chaos_drill_task.py` (register monthly schtask)
2. One real drill: run from White, kill local portal, verify <60s recovery via watchdog/schtask auto-restart
3. Ledger record

## Runbook note
chaos_drill.py kill_portal_on was a no-op stub for all hosts except Red; now uses taskkill (local) or elev.py+PowerShell (remote). False PASS risk eliminated.