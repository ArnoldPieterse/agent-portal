#!/usr/bin/env python3
"""deploy_boot_task_remotes.py - One-shot remote deployment of FleetBootRecovery task.

Run FROM WHITE non-sandbox admin session:
    python memory/ops/deploy_boot_task_remotes.py

What it does per remote (Pale .39, Black .99):
  1. Connects via WinRM (port 5985, NTLM)
  2. Creates C:\FleetOps\ if missing
  3. Copies boot_recovery.py + fleet_reload.py to C:\FleetOps\\
  4. Registers ONSTART scheduled task: FleetBootRecovery
  5. Verifies task exists via schtasks /query
  6. Appends result to memory/ops/boot-deploy-verify.jsonl

Prerequisites:
  - Run as admin on White (for WinRM outbound)
  - pip install pywinrm  (already installed per prior sessions)
  - Remotes must be powered on and reachable on :5985
  - Red (.245) is excluded (powered off; add manually when back)

Idempotent: safe to re-run; /f flag overwrites existing task.
"""
import json, os, sys, time, base64

HOSTS = {
    "PALE":  {"ip": "192.168.1.39", "user": "pale",  "pw": "131991Apiet"},
    "BLACK": {"ip": "192.168.1.99", "user": "black", "pw": "131991Apiet"},
}
# Red excluded (powered off as of 2026-11-17). Add when back:
#   "RED": {"ip": "192.168.1.245", "user": "red", "pw": "131991Apiet"},

REMOTE_DIR = r"C:\FleetOps"
TASK_NAME = "FleetBootRecovery"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boot-deploy-verify.jsonl")

def file_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def deploy_one(host_name, cfg):
    """Deploy boot-recovery to one remote host. Returns result dict."""
    import winrm
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    s = winrm.Session(
        f"http://{cfg['ip']}:5985/wsman",
        auth=(cfg["user"], cfg["pw"]),
        transport="ntlm"
    )

    result = {"ts": ts, "host": host_name, "checks": {}, "verdict": ""}

    # 1. Create remote dir
    r = s.run_cmd("cmd", ["/c", f'if not exist "{REMOTE_DIR}" mkdir "{REMOTE_DIR}"'])
    result["checks"]["dir_created"] = (r.status_code == 0)

    # 2. Copy boot_recovery.py (base64 -> file)
    local_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boot_recovery.py")
    if not os.path.exists(local_script):
        result["verdict"] = f"FAIL: local boot_recovery.py not found at {local_script}"
        return result
    b64 = file_to_b64(local_script)
    # PowerShell to decode base64 and write file
    ps_cmd = (
        f"$b = '{b64}'; "
        f"$bytes = [Convert]::FromBase64String($b); "
        f"[IO.File]::WriteAllBytes('{REMOTE_DIR}\\boot_recovery.py', $bytes)"
    )
    r2 = s.run_cmd("powershell", ["-NoProfile", "-Command", ps_cmd])
    result["checks"]["boot_script"] = (r2.status_code == 0)

    # 3. Copy fleet_reload.py if exists locally
    local_reload = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fleet_reload.py")
    if os.path.exists(local_reload):
        b64r = file_to_b64(local_reload)
        ps_cmd_r = (
            f"$b = '{b64r}'; "
            f"$bytes = [Convert]::FromBase64String($b); "
            f"[IO.File]::WriteAllBytes('{REMOTE_DIR}\\fleet_reload.py', $bytes)"
        )
        r3 = s.run_cmd("powershell", ["-NoProfile", "-Command", ps_cmd_r])
        result["checks"]["reload_script"] = (r3.status_code == 0)
    else:
        result["checks"]["reload_script"] = False

    # 4. Find python on remote (try common paths)
    r4 = s.run_cmd("cmd", ["/c", "where python"])
    py_out = r4.std_out.decode().strip()
    py_exe = py_out.splitlines()[0].strip() if py_out else "python"
    result["checks"]["python"] = bool(py_out)

    # 5. Register ONSTART scheduled task
    task_cmd = (
        f'schtasks /create /tn "{TASK_NAME}" '
        f'/tr "\"{py_exe}\" \"{REMOTE_DIR}\\boot_recovery.py\"" '
        f'/sc onstart /ru SYSTEM /rl HIGHEST /f'
    )
    r5 = s.run_cmd("cmd", ["/c", task_cmd])
    result["checks"]["schtask"] = (r5.status_code == 0)

    # 6. Verify task exists
    r6 = s.run_cmd("schtasks", ["/query", "/tn", TASK_NAME, "/fo", "LIST"])
    result["checks"]["verified"] = (r6.status_code == 0 and TASK_NAME in r6.std_out.decode())

    # Verdict
    passed = sum(1 for v in result["checks"].values() if v)
    total = len(result["checks"])
    result["verdict"] = f"{'PASS' if passed == total else 'INCOMPLETE'} ({passed}/{total})"

    return result


def main():
    results = []
    all_pass = True
    for host_name, cfg in HOSTS.items():
        print(f"[{time.strftime('%H:%M:%S')}] Deploying to {host_name} ({cfg['ip']})...")
        try:
            res = deploy_one(host_name, cfg)
        except Exception as e:
            res = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "host": host_name,
                   "checks": {}, "verdict": f"ERROR: {str(e)[:200]}"}
        results.append(res)
        print(f"  {res['verdict']}")
        if "PASS" not in res["verdict"]:
            all_pass = False

    # Append to jsonl log
    with open(LOG_FILE, "a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nResults appended to {LOG_FILE}")
    if all_pass:
        print("ALL HOSTS PASS - boot-recovery deployed.")
    else:
        print("Some hosts INCOMPLETE - check log above.")
    sys.exit(0 if all_pass else 1)

if __name__ == "__main__":
    main()
