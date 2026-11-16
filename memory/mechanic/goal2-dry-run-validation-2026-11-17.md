# Goal 2 Progress: --dry-run chain validation (2026-11-17)
Parent: memory/goals/mechanic.md. Sibling: goal2-boot-recovery-adaptive-wiring-2026-11-17.md.

## What was done
Added `--dry-run` mode to `memory/ops/boot_recovery.py`. Validates the full recovery chain without needing Studio or admin:
1. fleet_reload.py exists + is valid Python (ast.parse)
2. Host-matching logic resolves hostname to correct script path
3. Log directory is writable
4. deploy_boot_task.py exists for real-host registration

## Result on Red (this sandbox)
```
DRY_RUN_COMPLETE all_pass=True
checks: fleet_reload_exists=T, fleet_reload_valid_python=T, host_resolves=T,
        resolved_script=memory\ops\fleet_reload.py, log_writable=T, deploy_script_exists=T
```
12/12 unit tests (boot_recovery_test.py) still pass.

## Why this matters
Gives ops a one-command post-deployment health check: `python boot_recovery.py --dry-run` on any host confirms the chain is intact without requiring Studio to be up or COM/schtasks access. Reduces the "is it actually going to work?" gap before real reboot tests.

## Remaining for full closure (unchanged)
- [ ] Register FleetBootRecovery ONSTART task on Pale/Black/Red (needs admin + working COM)
- [ ] 3 production cold-boot runs with timestamped evidence
- [ ] Red .245 physical power-on

## One-line runbook
boot_recovery.py --dry-run = zero-dependency chain validator; run on any host post-deploy to confirm scripts are in place and hostname routing works before trusting a real reboot test.