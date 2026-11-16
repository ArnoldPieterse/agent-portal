# Goal 2 Progress: Startup-folder deployment path created (2026-11-17)

Parent: memory/goals/mechanic.md. Sibling: goal2-fleet-reload-created-2026-11-17.md.

## What was done this pass
1. **Created `memory/ops/deploy_startup_folder.py`** (89 lines) - non-admin alternative to deploy_boot_task.py. Places a .vbs in %APPDATA% Startup that runs boot_recovery.py at user logon with configurable delay. Works without COM/admin.
2. **Created `memory/ops/boot-deployment-runbook.md`** (63 lines) - per-host status table + 3 deployment paths (admin schtask, startup folder, manual test) + cold-boot test procedure + known blockers.
3. **Confirmed sandbox limitations**: APPDATA not set in sandbox (can't deploy locally), COM broken (0xC0000022), network blocked to :8099 and remote hosts.

## Remaining for closure
- Run `python memory/ops/deploy_startup_folder.py` on Pale, Black, Red from a real seat (not sandbox).
- Power on Red .245.
- 3 cold-boot tests with timestamped evidence (one per remote host).

## Next concrete step (next pass or from real seat)
From any non-sandbox seat: `python memory/ops/deploy_startup_folder.py --delay 15` then reboot that host and verify log entry in boot-recovery-log.jsonl.