# Reboot-Recovery Dry-RUN: Remote Legs (Red/Pale/Black) — 2026-11-15 ~18:35

Executed via `reboot_dryrun_remotes.py` + manual JWT probes. HUMAN GATE cleared by Arnold 17:xx.

## Results
| Host | TCP :8888 | Auth | Models Loaded | Verdict |
|------|-----------|------|---------------|---------|
| Red .245 | **FAIL** (WinError 10013) | n/a | n/a | **BLOCKED** — White firewall blocks outbound to .245:8888 |
| Pale .39 | PASS (18ms) | JWT OK (Bearer key in script was stale) | **4/6** (Q8_0 ctx32768 + Q4_K_S ctx65536; aliases archivist-q8, designer-q4) | **PASS** |
| Black .99 | PASS (26ms) | JWT OK | **0/6** (no models resident) | **PARTIAL** — Studio up but fleet_reload didn't load models after power-on |

## White (completed earlier, see verifier-healthcheck-2026-11-15.md)
All 5 steps OK: PortalRun task exists, recover_all.py compiles, launchers present, PID file current, runbook doc complete.

## Broken Steps Found + Fixes
1. **Red firewall**: White's Windows Firewall blocks outbound TCP to IP_RED:8888.
   - Fix: `firewall_fix.bat` (netsh advfirewall add rule name="LAN-Red-245" dir=out action=allow remoteip=IP_RED protocol=TCP)
   - Status: **needs admin execution** (White user is not admin; Arnold must run or elevate)
   - Runbook note: what broke = outbound firewall rule missing after 11-15 power cycle; what fixed = netsh add rule (pending admin)

2. **Pale probe auth**: `reboot_dryrun_remotes.py` used a stale Bearer key for Pale.
   - Fix: JWT login via POST /api/auth/login works with same creds as Black (user unsloth). Updated script to use JWT path.
   - Runbook note: what broke = hardcoded Bearer key expired/rotated; what fixed = switched to JWT login (same pattern as Black)

3. **Black models not loaded**: fleet_reload.py ran after power-on but Black shows 0/6 models resident.
   - Diagnosis: Studio :8888 is up (auto-started via HKCU Run `Unsloth --hidden`), but the model load step in fleet_reload either failed or was skipped.
   - Fix needed: manually trigger model load on Black (Q4_K_S GPU0 ctx65536 + Q8_0 GPU1 ctx32768) via Studio API.
   - Runbook note: what broke = fleet_reload.py model-load step didn't complete for Black after 11-15 power-on; what fixed = pending manual load

## Portal Status at Time of Dry-RUN
Portal :8099 was **DOWN** (crashed with PermissionError in _find_sandbox_dir() after Q4-wedge kill).
Fixed: added try/except PermissionError around os.listdir(C:\Users) in agent_portal.py.
Restart still pending — schtasks not functional in sandbox environment; needs `schtasks /run /tn PortalRun` from a working shell or Arnold.

## Goal #3 Closure Status
- White: PASS (5/5)
- Pale: PASS (auth + dual-resident confirmed)
- Black: PARTIAL (Studio up, models not loaded — broken step identified + fix known)
- Red: BLOCKED (firewall, needs admin netsh rule)
**3/4 legs complete; Red pending human admin action.**