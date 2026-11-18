#!/usr/bin/env python3
"""deploy_reboot_recovery_all.py - Deploy reboot_recover.py + register FleetBootRecovery schtask on ALL 4 fleet hosts.

Run FROM WHITE (admin or via elev):
    python memory/mechanic/deploy_reboot_recovery_all.py

Verify-only (check status without making changes, safe from any seat):
    python memory/mechanic/deploy_reboot_recovery_all.py --verify-only

What it does:
  - Local (White): registers schtask directly via schtasks
  - Remote (Pale/Black/Red): connects via WinRM, copies script, registers task
  - Idempotent: /f flag overwrites existing tasks
  - Logs results to memory/mechanic/reboot-recovery.jsonl

Prereqs: none (uses reboot_recover.py --register-task for self-registration).
For remote hosts, copy the script via any method (SMB, WinRM file transfer, USB) then run:
    python reboot_recover.py --register-task
on each host as admin.

This script automates the full sequence if pywinrm IS available; otherwise it prints
the manual steps needed per host.
"""
import json, os, sys, time, base64, subprocess, platform, datetime, pathlib

TASK_NAME = "FleetBootRecovery"
SCRIPT_SRC = pathlib.Path(__file__).parent / "reboot_recover.py"
LOG_FILE = pathlib.Path(__file__).parent / "reboot-recovery.jsonl"
REMOTE_DIR = r"C:\FleetOps"

HOSTS_REMOTE = {
    "PALE":  {"ip": "IP_PALE",  "user": "pale",  "pw": "[REDACTED-CREDENTIAL]"},
    "BLACK": {"ip": "IP_BLACK",  "user": "black", "pw": "[REDACTED-CREDENTIAL]"},
    "RED":   {"ip": "IP_RED", "user": "red",   "pw": "[REDACTED-CREDENTIAL]"},
}

def log_entry(entry):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def deploy_local():
    """Register task on the local host (White)."""
    script_path = str(SCRIPT_SRC.resolve())
    py_exe = sys.executable
    cmd = [
        "schtasks", "/create",
        "/tn", TASK_NAME,
        "/tr", f'"{py_exe}" "{script_path}"',
        "/sc", "onstart",
        "/ru", "SYSTEM",
        "/rl", "HIGHEST",
        "/f",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    ok = r.returncode == 0
    # Verify
    v = subprocess.run(["schtasks", "/query", "/tn", TASK_NAME, "/fo", "LIST"],
                       capture_output=True, text=True)
    verified = v.returncode == 0 and TASK_NAME in v.stdout
    return {"host": "WHITE (local)", "registered": ok, "verified": verified,
            "error": r.stderr.strip() if not ok else ""}

def deploy_remote(name, cfg):
    """Deploy to a remote host via WinRM."""
    try:
        import winrm
    except ImportError:
        return {"host": name, "registered": False, "verified": False,
                "error": "pywinrm not installed on this host"}
    
    s = winrm.Session(
        f"http://{cfg['ip']}:5985/wsman",
        auth=(cfg["user"], cfg["pw"]),
        transport="ntlm"
    )
    
    # Create remote dir
    s.run_cmd("cmd", ["/c", f'if not exist "{REMOTE_DIR}" mkdir "{REMOTE_DIR}"'])
    
    # Copy reboot_recover.py via base64
    with open(SCRIPT_SRC, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ps_cmd = (
        f"$b = '{b64}'; "
        f"$bytes = [Convert]::FromBase64String($b); "
        f"[IO.File]::WriteAllBytes('{REMOTE_DIR}\\reboot_recover.py', $bytes)"
    )
    s.run_cmd("powershell", ["-NoProfile", "-Command", ps_cmd])
    
    # Find python on remote
    r_py = s.run_cmd("cmd", ["/c", "where python"])
    py_out = r_py.std_out.decode().strip()
    py_exe = py_out.splitlines()[0].strip() if py_out else "python"
    
    # Register task
    task_cmd = (
        f'schtasks /create /tn "{TASK_NAME}" '
        f'/tr "\"{py_exe}\" \"{REMOTE_DIR}\\reboot_recover.py\"" '
        f'/sc onstart /ru SYSTEM /rl HIGHEST /f'
    )
    r_task = s.run_cmd("cmd", ["/c", task_cmd])
    
    # Verify
    r_verify = s.run_cmd("schtasks", ["/query", "/tn", TASK_NAME, "/fo", "LIST"])
    verified = r_verify.returncode == 0 and TASK_NAME in r_verify.std_out.decode()
    
    return {"host": name, "registered": r_task.status_code == 0,
            "verified": verified, "python": py_exe}

def verify_local():
    """Check if FleetBootRecovery task exists on local host."""
    v = subprocess.run(["schtasks", "/query", "/tn", TASK_NAME, "/fo", "LIST"],
                       capture_output=True, text=True)
    ok = v.returncode == 0 and TASK_NAME in v.stdout
    return {"host": "WHITE (local)", "verified": ok,
            "detail": v.stdout.strip()[:200] if ok else v.stderr.strip()[:100]}

def verify_only():
    """Verify deployment status: local schtasks + jsonl log for remotes."""
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(f"[{ts}] VERIFY-ONLY mode (no changes made)\n")
    
    # Local
    res_local = verify_local()
    print(f"  {res_local['host']}: {'PASS' if res_local['verified'] else 'FAIL'}")
    if not res_local["verified"]:
        print(f"    detail: {res_local.get('detail','')}")
    
    # Remote: check jsonl log for most recent deployment results
    remote_status = {}
    if LOG_FILE.exists():
        last_deploy = None
        with open(LOG_FILE) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "deploy_reboot_recovery_all":
                        last_deploy = entry
                except json.JSONDecodeError:
                    continue
        if last_deploy:
            print(f"\n  Last deployment logged: {last_deploy['ts']}")
            for host, res in last_deploy.get("results", {}).items():
                if "local" in host.lower():
                    continue
                ok = res.get("verified", False)
                remote_status[host] = ok
                mark = 'PASS' if ok else 'FAIL'
                err = f" ({res.get('error','')[:60]})" if not ok else ""
                print(f"  {host}: {mark}{err}")
        else:
            print("\n  No deployment found in reboot-recovery.jsonl")
    else:
        print("\n  reboot-recovery.jsonl not found - no prior deployment logged")
    
    all_ok = res_local["verified"] and all(remote_status.values()) if remote_status else res_local["verified"]
    total = 1 + len(remote_status)
    passed = (1 if res_local["verified"] else 0) + sum(1 for v in remote_status.values() if v)
    print(f"\nSummary: {passed}/{total} hosts verified")
    return 0 if all_ok else 1

def main():
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    if "--verify-only" in sys.argv:
        sys.exit(verify_only())
    
    results = []
    
    # Local (White)
    print(f"[{ts}] Deploying to local host...")
    res_local = deploy_local()
    results.append(res_local)
    print(f"  {res_local['host']}: registered={res_local['registered']} verified={res_local['verified']}")
    
    # Remotes
    for name, cfg in HOSTS_REMOTE.items():
        print(f"[{ts}] Deploying to {name} ({cfg['ip']})...")
        try:
            res = deploy_remote(name, cfg)
        except Exception as e:
            res = {"host": name, "registered": False, "verified": False, "error": str(e)[:200]}
        results.append(res)
        print(f"  {name}: registered={res.get('registered')} verified={res.get('verified')}")
    
    # Log
    entry = {"ts": ts, "type": "deploy_reboot_recovery_all",
             "results": {r["host"]: r for r in results},
             "all_verified": all(r.get("verified", False) for r in results)}
    log_entry(entry)
    
    passed = sum(1 for r in results if r.get("verified"))
    print(f"\nSummary: {passed}/{len(results)} hosts verified")
    sys.exit(0 if passed == len(results) else 1)

if __name__ == "__main__":
    main()
