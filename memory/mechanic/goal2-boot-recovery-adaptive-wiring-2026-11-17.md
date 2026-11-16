# Goal #2 Progress: Adaptive Boot-Recovery Wiring — 2026-11-17
Seat: White sandbox. Status: IN PROGRESS.

## What was done this pass
1. **Adaptive timeout added** to `boot_recovery.py`: `_adaptive_timeout()` reads historical boot times from `boot-recovery-log.jsonl`, computes 1.5x average of last 5 boots (floor 60s, ceiling 600s), falls back to 300s default. Logged as `adaptive_timeout` event.
2. **Scheduled-task registration script** created: `memory/ops/boot_recovery_register.bat` — registers `FleetBootRecovery` ONSTART task (SYSTEM, HIGHEST) on any host with admin. Idempotent (deletes existing first).
3. **VBS fallback** for non-admin hosts: `memory/ops/boot_recovery.vbs` — place in Startup folder; waits 3 min then runs recovery hidden.
4. **Test suite updated + all pass**: 12/12 (`boot_recovery_test.py`).

## Remaining for full closure
- [ ] Deploy ONSTART task on Pale, Black, Red (requires admin access or VBS fallback placement)
- [ ] 3 production runs from non-sandbox seats (need at least one real reboot per remote host with timestamped evidence in boot-recovery-log.jsonl)
- [ ] Red .245 still powered off — its leg stays open until host is back

## Files touched
- `memory/ops/boot_recovery.py` — added `_adaptive_timeout()`, changed `wait_studio()` signature, updated `main()` call
- `memory/mechanic/boot_recovery_test.py` — updated expected event sequence (+adaptive_timeout)
- `memory/ops/boot_recovery_register.bat` — NEW: ONSTART task registration script
- `memory/ops/boot_recovery.vbs` — NEW: non-admin fallback for Startup folder deployment
