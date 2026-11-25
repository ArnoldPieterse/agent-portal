# Goal 2 progress - 2026-11-16 (Mechic auto-loop)

## What was done this turn
- Reviewed boot_recovery.py (exists, correct logic: wait Studio :8888, invoke fleet_reload.py, verify portal :8099)
- Wrote memory/ops/deploy_boot_task.py -- idempotent ONSTART task registration script (schtasks /create /sc onstart /ru SYSTEM)
  - Per-host deployment: run on each of White/Pale/Black/Red with admin rights
  - Includes verify() step that confirms task presence post-registration
- Attempted remote probe (Pale .39, Black .99, Red .245 :445) -- sandbox blocks non-allowlisted network destinations this session

## Blockers (exact unblock steps)
1. schtasks COM unavailable in sandbox -> need to run deploy_boot_task.py via WinRM/RDP on each host, OR from a terminal with COM available
2. Red (.245) was powered off as of last dry-run (2026-11-16 earlier) -> re-probe when back up

## Status
- White: boot_recovery.py logic verified (prior session); deploy_boot_task.py ready
- Pale/Black: reachable per prior probe; deploy script ready
- Red: powered off (last known state)

Next concrete step when unblocked: winrs admin@IP_PALE "python C:\memory\ops\deploy_boot_task.py" (repeat for .99, .245)
