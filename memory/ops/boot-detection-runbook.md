# Boot-Detection Scheduled Task — Registration Runbook
Updated: 2026-11-17 (Mechanic, goal #2)

## What it does
`boot_recovery.py` runs at system startup on each host. If uptime < 5 min,
it waits for Studio :8888 then invokes `fleet_reload.py` (idempotent).
Logs to `memory/ops/boot-recovery.jsonl`.

## Registration (run ON EACH HOST, as the local user)

### White
```
schtasks /create /tn "FleetBootRecovery" /tr "python C:\path\to\agent_portal\boot_recovery.py" /sc onstart /ru White /rl limited /f
```

### Black (run via WinRM or RDP as `black` user)
```
schtasks /create /tn "FleetBootRecovery" /tr "python C:\path\to\agent_portal\boot_recovery.py" /sc onstart /ru black /rl limited /f
```
Set env var `FLEET_HOST=Black` in the task's environment (or edit HOST_IP lookup).

### Pale (as `pale` user)
```
schtasks /create /tn "FleetBootRecovery" /tr "python C:\path\to\agent_portal\boot_recovery.py" /sc onstart /ru pale /rl limited /f
```
Set env var `FLEET_HOST=Pale`.

### Red (as `Red` user)
```
schtasks /create /tn "FleetBootRecovery" /tr "python C:\path\to\agent_portal\boot_recovery.py" /sc onstart /ru Red /rl limited /f
```
Set env var `FLEET_HOST=Red`.

## Verification
1. On each host: `schtasks /query /tn FleetBootRecovery` — confirm it exists.
2. Reboot one host (start with Pale, lowest risk).
3. Within 5 min of boot: check `memory/ops/boot-recovery.jsonl` for a `reload_done` entry.
4. Confirm Studio :8888 has dual models loaded via portal smoke test.

## Notes
- The script is idempotent: if models are already loaded (e.g. Studio auto-restored),
  fleet_reload.py detects this and skips. Safe to leave the task always-on.
- If a host is down at boot time (Studio takes >10 min), the task logs FAIL_studio_never_up
  and exits non-zero. The PortalWatchdog (5-min cadence) will catch it separately.
- Red (.245) was powered off as of 2026-11-16; register its task when the host returns.
