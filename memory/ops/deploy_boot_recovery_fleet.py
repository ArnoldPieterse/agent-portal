#!/usr/bin/env python3
"""deploy_boot_recovery_fleet.py - Register FleetBootRecovery schtask on all 4 fleet hosts.

Run from a NON-SANDBOX White seat (has admin + LAN egress).
Registers locally first, then attempts remote registration via WinRM/PowerShell.
Logs evidence to memory/mechanic/goal4-fleet-deploy-<date>.jsonl.

Usage:
    python memory/ops/deploy_boot_recovery_fleet.py [--dry-run]
"""
import json, subprocess, datetime, sys, os, platform

HOSTS = {
    "White": {"ip": "127.0.0.1", "local": True},
    "Pale":  {"ip": "IP_PALE", "local": False},
    "Black": {"ip": "IP_BLACK", "local": False},
    "Red":   {"ip": "IP_RED", "local": False},
}

LOG_PATH = os.path.join("memory", "mechanic", f"goal4-fleet-deploy-{datetime.date.today().isoformat()}.jsonl")

def log(event, **kw):
    entry = {"ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "event": event, **kw}
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"  [{entry['ts']}] {event} {kw}", flush=True)

def register_local(dry_run=False):
    """Register FleetBootRecovery on this host (White)."""
    if dry_run:
        log("DRY_RUN", host="White", action="register_local")
        return True
    bat = os.path.join(os.path.dirname(__file__), "boot_recovery_register.bat")
    result = subprocess.run(["cmd", "/c", bat], capture_output=True, text=True, timeout=30)
    ok = "OK" in result.stdout or "registered" in result.stdout.lower()
    log("register_local", host="White", success=ok, output=result.stdout.strip()[-200:])
    return ok

def register_remote(hostname, ip, dry_run=False):
    """Attempt remote registration via PowerShell scheduled task creation."""
    if dry_run:
        log("DRY_RUN", host=hostname, action=f"register_remote {ip}")
        return True
    # Use PowerShell to run schtasks on the remote host via WinRM
    ps_cmd = (
        f"$action = New-ScheduledTaskAction -Execute 'pythonw.exe' "
        f"-Argument '\\\\\{ip}\\\\C$\\\\Projects\\\\Workspace\\\\memory\\\\ops\\\\boot_recovery.py'; "
        f"$trigger = New-ScheduledTaskTrigger -AtStartup; "
        f"$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest; "
        f"Register-ScheduledTask -TaskName 'FleetBootRecovery' -Action $action -Trigger $trigger -Principal $principal -Force"
    )
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"Invoke-Command -ComputerName '{ip}' -Credential (Get-Credential -UserName 'arnold' -Message 'SMB') -ScriptBlock {{ {ps_cmd} }}"],
            capture_output=True, text=True, timeout=60
        )
        ok = "FleetBootRecovery" in result.stdout and "ERROR" not in result.stderr.upper()
        log("register_remote", host=hostname, ip=ip, success=ok,
            stdout=result.stdout[-200:], stderr=result.stderr[-100:] if result.stderr else "")
        return ok
    except subprocess.TimeoutExpired:
        log("register_remote_timeout", host=hostname, ip=ip)
        return False
    except Exception as e:
        log("register_remote_error", host=hostname, ip=ip, error=str(e)[:200])
        return False

def verify_task(hostname, ip, dry_run=False):
    """Verify the task exists and is in Ready state."""
    if dry_run:
        return True
    try:
        if hostname == "White":
            r = subprocess.run(["schtasks", "/query", "/tn", "FleetBootRecovery"],
                             capture_output=True, text=True, timeout=10)
            ok = "FleetBootRecovery" in r.stdout and "ERROR" not in r.stderr
        else:
            r = subprocess.run(
                ["powershell", "-Command",
                 f"Invoke-Command -ComputerName '{ip}' -ScriptBlock {{ Get-ScheduledTask -TaskName 'FleetBootRecovery' | Select-Object TaskName, State }}"],
                capture_output=True, text=True, timeout=30
            )
            ok = "Ready" in r.stdout or "Running" in r.stdout
        log("verify", host=hostname, exists=ok)
        return ok
    except Exception as e:
        log("verify_error", host=hostname, error=str(e)[:100])
        return False

def main():
    dry_run = "--dry-run" in sys.argv
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"=== FleetBootRecovery fleet deployment ({mode}) ===")
    log("deploy_start", mode=mode, initiated_by=platform.node())

    results = {}
    for name, info in HOSTS.items():
        print(f"\n[{name}] {info['ip']}")
        if info["local"]:
            ok = register_local(dry_run)
        else:
            ok = register_remote(name, info["ip"], dry_run)
        if ok and not dry_run:
            ok = verify_task(name, info["ip"])
        results[name] = ok

    print(f"\n=== Summary ===")
    for name, ok in results.items():
        status = "OK" if ok else "FAIL/PENDING"
        print(f"  {name:8}: {status}")
    log("deploy_complete", results=results)

if __name__ == "__main__":
    main()
