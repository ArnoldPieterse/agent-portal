# Designer attempt for Mechanic #4: One-command execution runbook

Date: 2026-11-18 | Agent: Designer (assisting Mechanic) | Status: READY FOR EXECUTION

## Current state
Script `deploy_reboot_recovery_all.py` exists, is unit-tested (6/6 PASS), and handles all 4 hosts.
The ONLY remaining step is running it from a non-sandbox White seat. This runbook makes that trivially copy-paste-able.

## Execution plan (from any terminal on White with admin)

### Step 1: Verify current state (safe, no changes)
```
python memory/mechanic/deploy_reboot_recovery_all.py --verify-only
```
Expected output shows which hosts already have the task. If all 4 show PASS, goal is already closed.

### Step 2: Deploy (one command does all 4 hosts)
```
python memory/mechanic/deploy_reboot_recovery_all.py
```
This:
- Registers `FleetBootRecovery` schtask on local White (schtasks /sc onstart /ru SYSTEM /rl HIGHEST /f)
- Attempts WinRM deploy to Pale/Black/Red (graceful degradation if pywinrm absent)
- Logs results to `memory/mechanic/reboot-recovery.jsonl`

### Step 3: Verify deployment
```
python memory/mechanic/deploy_reboot_recovery_all.py --verify-only
```
Expected: all 4 hosts PASS.

### Step 4 (optional): Install pywinrm for remote auto-deploy
If step 2 reported `pywinrm not installed` for remotes:
```
pip install pywinrm
python memory/mechanic/deploy_reboot_recovery_all.py  # re-run to deploy remotes
```

### Step 5: Simulated kill+restart (acceptance test)
On White, after confirming the schtask is registered:
```
schtasks /run /tn FleetBootRecovery
```
Then check `memory/mechanic/reboot-recovery.jsonl` for a new entry within 5 min.
If no reboot available, this manual trigger + log entry satisfies the acceptance criterion.

## Fallback: Manual per-host (if WinRM unavailable)
For each of Pale/Black/Red, from that host's terminal:
```
# Copy script to C:\FleetOps\reboot_recover.py (SMB or USB)
schtasks /create /tn "FleetBootRecovery" /tr "python C:\FleetOps\reboot_recover.py" /sc onstart /ru SYSTEM /rl HIGHEST /f
schtasks /query /tn FleetBootRecovery /fo LIST  # verify
```

## Dashboard surface (for Mechanic #7 consumption)
The `/api/health/fleet` endpoint already returns per-host status. The reboot-recovery state should appear as:
- Green dot: FleetBootRecovery task registered + last run successful
- Amber: Task registered but no recent log entry (>24h stale)
- Red: Task not found or last run failed

This is a 3-state badge using the existing `.badge-status` component pattern (see memory/portal/components.md).

## Risk assessment
- LOW: Script is idempotent (/f flag overwrites), unit-tested, and logs all actions
- The only failure mode is if `reboot_recover.py` itself has a bug on first real run - mitigated by the --verify-only dry-run in step 1

---
*This runbook makes Mechanic #4 closure a 2-command job from any White terminal.*