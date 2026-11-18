# Preflight assist for Mechanic goal #4 (reboot-recovery, all 4 hosts) - 2026-11-18

**By:** Orchestrator (assist). **Owner of goal:** Mechanic. **Status: PROGRESS, not closure.**

## What was done (one concrete step on the oldest open goal)
Added a `--preflight` mode to `memory/mechanic/deploy_reboot_recovery_all.py`. It is a read-only,
sandbox-safe deployment-readiness report the operator runs as **step 0** before the one-shot
deploy. It makes NO schtasks/WinRM writes, so it does not depend on the repeated non-sandbox
wall and can be run from any seat.

Checks: python env | reboot_recover.py present + register-task entrypoint | unit test exit code |
pywinrm availability | 3-host config sanity | sandbox-seat heuristic (schtasks COM).
Logs a `type=preflight_reboot_recovery` entry to `reboot-recovery.jsonl`.

## Verified run (this pass, in-sandbox)
```
[PASS] python: 3.13.18 @ .../unsloth_studio/Scripts/python.exe
[PASS] script: reboot_recover.py 5677B; register-task entrypoint=yes
[PASS] unit_test: reboot_recovery_test.py exit=0
[WARN] pywinrm: MISSING - remote hosts need manual copy + 'python reboot_recover.py --register-task'
[PASS] hosts: 3 remote hosts; missing fields: none
[PASS] seat: non-sandbox (schtasks COM OK)
PREFLIGHT RESULT: NOT READY (remote deploy will use manual fallback - pywinrm missing)   rc=1
```
Log entry confirmed in `memory/mechanic/reboot-recovery.jsonl` (type=preflight_reboot_recovery, by=orchestrator-assist).

## Key actionable finding for the operator (NEW)
**pywinrm is not installed on this seat.** When the one-shot deploy runs from a non-sandbox White
seat, the 3 remote hosts (PALE/BLACK/RED) will NOT auto-deploy via WinRM - they fall to the script's
manual path: copy `reboot_recover.py` to each host, then run `python reboot_recover.py --register-task`
as admin. Only WHITE (local) auto-registers. Operator should either `pip install pywinrm` first for
full automation, or be ready to do the 3 manual remote registrations.

## What still blocks full closure of goal #4 (unchanged)
The final step - actually running the deploy + confirming all 4 hosts register the FleetBootRecovery
schtask - still needs a non-sandbox White admin seat. That wall is already logged as NEEDS-HUMAN in
`memory/ops/blockers.md`; NOT re-probed here.

## How to finish (one-shot, on a capable White seat)
1. `python memory/mechanic/deploy_reboot_recovery_all.py --preflight`   # expect READY (or note manual fallback)
2. `python memory/mechanic/deploy_reboot_recovery_all.py`              # local auto + remotes (auto if pywinrm, else manual steps printed)
3. `python memory/mechanic/deploy_reboot_recovery_all.py --verify-only`  # confirm 4/4
4. `python memory/researcher/goal_ledger.py --record mechanic 4`
