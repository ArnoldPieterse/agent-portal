# Unblock-All Script Built (2026-11-23)

## What was built
`memory/mechanic/unblock_all.py` - single entry point that executes ALL remaining live legs in sequence:

| Phase | Goal(s) unblocked | What it does |
|-------|-------------------|--------------|
| 1. schtasks | #1, #2, #7 | Runs deploy_all_schtasks.py (registers PortalLoadProbe, MirrorHeal, LogRotateDaily, BootRecoverDetect, ChaosDrillMonthly) |
| 2. winrm_e2e | #3 | Runs winrm_e2e_test.py --host black (full anti-stall cycle: baseline -> down -> CB detect -> reboot -> recovery) |
| 3. cb_live | #4 | GET /api/fleet/status, verifies 200 + host rows + state=down for dead hosts |

## Usage (from non-sandbox White seat)
```
python memory/mechanic/unblock_all.py
# or selectively:
python memory/mechanic/unblock_all.py --skip-winrm --host pale
WINRM_PASSWORD=<pw> python memory/mechanic/unblock_all.py
```

## Verification this pass
- py_compile: PASS
- All referenced scripts exist: deploy_all_schtasks.py (154L), winrm_e2e_test.py (dry-run validated 2026-11-21)
- Phase independence: each phase catches its own exceptions; one failure does NOT block others
- Log output: memory/mechanic/unblock-all-YYYY-MM-DD.jsonl

## Status
Script is READY. Execution requires a non-sandbox White seat with:
- Task Scheduler COM (for schtasks)
- WinRM/PowerShell remoting to Black/Pale
- Portal listening on :8099

This is the single command that closes all 4 open Mechanic goals when run from the right seat.
