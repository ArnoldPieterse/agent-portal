# Goal #2 progress — deploy_boot_task.py hardening (2026-11-17)

## What was done this pass
1. **Fixed stale IPs** in `memory/ops/deploy_boot_task.py`: 10.0.0.x → 192.168.1.x (correct fleet addresses per host-port-task-map).
2. **Added `--remote` mode**: single command from White deploys to multiple hosts via `schtasks /s <IP>`:
   ```
   python deploy_boot_task.py --remote Pale Black Red
   ```
   Resolves hostnames (pale/black/red) to IPs; uses current user or `--user` for auth.
3. **Re-ran boot_recovery_test.py**: 12/12 PASS (hostname routing, log format, studio timeout, full flow).
4. **py_compile + --help** verified on updated script.

## Remaining (external dependency)
- Run `python deploy_boot_task.py --remote Pale Black` from White with admin (WinRM :5985 open on both).
- Red .245 still powered off — cannot deploy or test until host is back.
- One real cold-boot per remote = acceptance criterion for full closure.

## Runbook note
What broke: deploy_boot_task.py had wrong subnet (10.0.0.x) and no remote mode, making multi-host deployment a manual RDP exercise.
What fixed: corrected IPs + `--remote` batch mode; next admin session is one command per reachable host.

## Update 2026-11-25 - Orchestrator
Red .245 reported POWERED ON by human (see TODO.md top section). Red leg of `--remote ... Red` re-testable now. Still pending: real cold-boot on Red for full closure + probe confirmation of host status.