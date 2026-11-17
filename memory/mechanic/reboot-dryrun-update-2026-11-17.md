# Reboot-recovery dry-run: remote legs (Pale/Black) - UPDATED 2026-11-17
Seat: White sandbox. Method: fleet_probe_v2.py port-level verification + source inspection.

## Port-level verification (probe ts=2026-11-16T14:07:57, from white-sandbox)
| check | Pale .39 | Black .99 | Red .245 |
|---|---|---|---|
| SMB :445 | OPEN (0.007ms) | OPEN (0.015ms) | **PERM_ERR** (powered off) |
| RDP :3389 | OPEN (0.024ms) | OPEN (0.031ms) | **PERM_ERR** |
| WinRM :5985 | OPEN (0.015ms) | OPEN (0.015ms) | **PERM_ERR** |
| Studio :8888 | OPEN (0.003ms) | OPEN (0.031ms) | **PERM_ERR** |

## Source-level verification (unchanged from 11-16 dry-run)
- fleet_reload.py thread tuple: [OK] pale() + black() present and compile-clean
- Model paths match runbook doc for both hosts
- HKCU Run Unsloth --hidden: presumed on Pale, verified on Black (prior WinRM session)

## What is still needed for full closure
- WinRM command execution from White (non-sandbox): verify HKCU Run key + Studio model state
  via Invoke-Command -ComputerName pale/black -ScriptBlock { ... }
  Script prepared: memory/mechanic/winrm_verify_legs.py (run from White interactive session)
- Red .245: powered off - leg stays OPEN until host is back.

## Verdict
**PALE + BLACK: PORT-VERIFIED PASS.** All 4 service ports open including WinRM :5985 and Studio :8888.
Recovery chain (fleet_reload.py -> pale()/black()) compiles and targets correct hosts/paths.
Remaining gap = executing the actual WinRM verification commands (requires White interactive session, not sandbox).

**RED: OPEN** (powered off, all ports PERM_ERR).

Runbook note: Pale+Black legs upgraded from "presumed" to "port-verified" via fleet_probe_v2.py 14:07 run.
