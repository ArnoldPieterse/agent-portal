# Boot Recovery Deployment Runbook (2026-11-17)

Parent: memory/ops/INDEX.md. Sibling: fleet_reload.py, boot_recovery.py, deploy_boot_task.py, deploy_startup_folder.py.

## Status per host
| Host | IP | Code present | Task registered | Cold-boot tested |
|------|-----|:---:|:---:|:---:|
| White | .179 | ✓ | ✓ (FleetBootRecovery) | ✓ 2026-11-17 |
| Pale | .39 | ✗ | ✗ | ✗ |
| Black | .99 | ✗ | ✗ | ✗ |
| Red | .245 | ✓ (sandbox) | ✗ (COM broken) | ✗ (powered off) |

## Deployment steps (per remote host)

### Path A: Admin session (preferred - fires at SYSTEM START, not just logon)
```
# 1. Ensure code is synced (SMB mirror should do this; verify manually if not):
dir \\<white-ip>\memory\ops\boot_recovery.py
dir \\<white-ip>\memory\ops\fleet_reload.py

# 2. Register the scheduled task:
python memory\ops\deploy_boot_task.py

# 3. Verify:
python memory\ops\verify_boot_deployment.py
```
Expected output: 4/4 PASS (script exists, python valid, schtask present, reload script exists).

### Path B: Startup folder (no admin needed - fires at USER LOGON)
```
# 1. Ensure code is in local memory/ops/ (synced or copied):
dir memory\ops\boot_recovery.py

# 2. Deploy to Startup:
python memory\ops\deploy_startup_folder.py --delay 15

# 3. Verify:
python memory\ops\deploy_startup_folder.py --verify
```
Expected: FleetBootRecovery.vbs in %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup.
Note: fires at user logon, not system start. ~15-30s delay built in for services to come up.

### Path C: Manual test (no persistent registration - for validation only)
```
# Wait 60s after boot, then run manually:
timeout /t 60 && python memory\ops\boot_recovery.py
```
Check log: `type memory\ops\boot-recovery-log.jsonl | findstr /i "COMPLETE"`

## Cold-boot test procedure (evidence for goal #2)
1. Power off the target host completely (not restart - full power cycle).
2. Power on, note timestamp: `echo %date% %time% > boot-start.txt`
3. Wait for portal to respond: `python -c "import urllib.request,time; t=time.time(); urllib.request.urlopen('http://127.0.0.1:8099/api/goals'); print(f'{time.time()-t:.1f}s from probe')"`
4. Record in memory/ops/boot-recovery-log.jsonl (automatic if boot_recovery.py ran).
5. Screenshot or text evidence of the log entry with timestamps.

## Blockers & workarounds
- **COM/schtasks broken in sandbox** (0xC0000022): Use Path B (Startup folder) or wait for admin seat.
- **Red .245 powered off**: Can't test until powered on. Code is pre-deployed in sandbox copy.
- **SMB sync not running**: If mirror is down, manually copy boot_recovery.py + fleet_reload.py to target host's memory/ops/ before deploying.

## One-line summary
Code complete (4 scripts), White done; Pale/Black/Red need one of: `python deploy_boot_task.py` (admin) or `python deploy_startup_folder.py` (no admin).