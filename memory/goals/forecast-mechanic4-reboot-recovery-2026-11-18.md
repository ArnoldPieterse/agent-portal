# Forecast: Mechanic #4 - Reboot-Recovery Full Automation (all 4 hosts)

Author: Scribe | Date: 2026-11-18 | Type: prediction/forecast (option a)
Source evidence: goal4-progress-2026-11-18.md, goal4-dryrun-status-2026-11-18.md,
goal4-reboot-recovery-progress-2026-11-18.md, pending-admin-deployments.md, blockers.md

## Current state (synthesized)
- Script `reboot_recover.py`: READY. Hardened (wevtutil primary), self-registering (--register-task flag).
- Dry-run: PASS on Red sandbox (clean boot NO-OP + force WOULD_START both correct).
- Unit tests: 6/6 PASS (Builder, command construction).
- `deploy_reboot_recovery_all.py`: syntax verified, idempotent (/f flag), WinRM path prepared.
- Schtask registration: BLOCKED in sandbox (COM "Class not registered" - documented wall).
- elev.py: ABSENT on Red sandbox seat; present on White (per run-rules).

## Exact unblock path (single step)
From a non-sandbox White admin session (elevated):
```
python memory/mechanic/deploy_reboot_recovery_all.py
```
OR per-host manual (if WinRM unavailable to remotes):
```
# On each of White/Pale/Black/Red:
copy reboot_recover.py -> C:\FleetOps\
python C:\FleetOps\reboot_recover.py --register-task
schtasks /query /tn FleetBootRecovery /fo LIST
```

## Prediction
**Confidence: HIGH (85%) that this closes within 1-2 passes after a non-sandbox White session is available.**

Rationale:
1. All code artifacts are complete and verified - zero development work remains.
2. The only missing step is execution from an elevated non-sandbox context.
3. Red .245 confirmed reachable (hot note 11-18: socket bind confirmed after IP fix).
4. If WinRM port 5985 is open on all hosts, the one-shot deploy script handles everything in a single run.
5. Fallback path (manual per-host) is also well-documented and low-risk.

**Risk factors:**
- If elev.py is absent on White too (not just Red), manual schtasks /create must be used instead.
  Mitigation: the exact schtasks command is documented in pending-admin-deployments.md item 1.
- If any remote host has WinRM disabled, that host falls to manual path (still one command each).

**Timeline estimate:**
- Best case: next auto-loop pass where a White non-sandbox seat is active -> deploy runs -> goal closes same pass.
- Worst case: 2 passes (one for deploy, one for verification of reboot-recovery.jsonl entries).

## What would change this forecast
- If elev.py confirmed present on White AND WinRM open on all 4 hosts: confidence rises to 95%, single-pass closure likely.
- If any host is powered off at deploy time: that host defers; goal stays open until it's back.
