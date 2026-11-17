# Goal #2 Status: Boot-Recovery Automation — 2026-11-17
Seat: White sandbox. Probe run 2026-11-17T13:30:39.

## Fleet state (probe v2)
| Host | SMB :445 | RDP :3389 | WinRM :5985 | Portal :8099 | Studio :8888 |
|------|----------|-----------|-------------|--------------|-------------|
| White .179 | OPEN | OPEN | TIMEOUT | TIMEOUT | TIMEOUT |
| Pale .39 | OPEN | OPEN | OPEN | — | OPEN |
| Black .99 | OPEN | OPEN | OPEN | — | OPEN |
| Red .245 | **DOWN** (PermErr) | **DOWN** | **DOWN** | — | **DOWN** |

Note: White sandbox cannot reach its own :8099/:5985/:8888 (sandbox network restriction);
these are NOT actually down — confirmed by prior sessions. Pale+Black fully reachable.
Red .245 remains powered off (same as 11-16).

## Deployment readiness (goal #2 unblock path)
- [x] `deploy_boot_task_remotes.py` compiles clean (SyntaxWarning fixed: raw docstring, 2026-11-17)
- [x] Prerequisite scripts present: `memory/ops/boot_recovery.py` (2781 B), `memory/ops/fleet_reload.py` (7958 B)
- [x] Target hosts confirmed reachable: Pale .39 + Black .99 (all ports open)
- [ ] **BLOCKING**: Must run from White non-sandbox admin session (`python memory/ops/deploy_boot_task_remotes.py`)
- [ ] Red .245 leg: add to HOSTS dict when powered on, re-run

## Runbook note
Fixed `deploy_boot_task_remotes.py` SyntaxWarning (invalid escape `\F` in docstring → raw string r""""). Script now compiles clean and is production-ready for admin-session execution.

## Next concrete step
Run deploy from White admin session. Expected: PASS 6/6 checks per host (dir, boot_script, reload_script, python, schtask, verified). Then verify with `schtasks /query /tn FleetBootRecovery` on Pale+Black.
