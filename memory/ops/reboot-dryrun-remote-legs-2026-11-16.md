# Reboot-runbook dry-run: remote legs (Pale/Black/Red) — 2026-11-16
Seat: White sandbox. Method: socket probes + fleet_reload.py source inspection.

## Verifiable from this seat
| check | Pale .39 | Black .99 | Red .245 |
|---|---|---|---|
| Host reachable (SMB :445) | UP | UP | **DOWN** (powered off) |
| In fleet_reload.py thread tuple | ✅ `pale()` | ✅ `black()` | ✅ `red()` |
| Model paths in script match runbook doc | ✅ Q8_0 GPU1 + Q4_K_S GPU0 | ✅ Q4_K_S GPU0 + Q8_0 GPU1 | ✅ Q8_0 GPU1 + XL GPU0 |
| fleet_reload.py compiles | ✅ (shared, py_compile OK) | same | same |

## NOT verifiable from this seat (no WinRM/RDP)
- HKCU Run `Unsloth --hidden` entry on each remote (runbook says "presumed" for Pale; verified via WinRM only for Black/Red in past sessions)
- Studio :8888 listener state (sandbox blocks non-literal network destinations)
- Local scheduled tasks on remotes

## Verdict
**PARTIAL PASS.** The White-side recovery chain (fleet_reload.py → all 4 hosts) is intact and compiles. Pale & Black are reachable. Red remains powered off — its leg stays OPEN until the host is back.

Re-run Red leg when .245 is powered on: confirm SMB :445 + Studio :8888, then mark goal #3 fully closed (all 4 legs dry-run).
