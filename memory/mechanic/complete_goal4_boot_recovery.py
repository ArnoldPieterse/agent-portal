#!/usr/bin/env python3
"""complete_goal4_boot_recovery.py - One-shot: register FleetBootRecovery on all 4 hosts.

Run FROM WHITE in an elevated/admin session (or via elev.py):
    python memory/mechanic/complete_goal4_boot_recovery.py

What it does:
  1. Copies boot_recovery.py to C:\FleetOps\ on White (local)
  2. Registers FleetBootRecovery ONSTART schtask on White
  3. Deploys to Pale (.39) + Black (.99) + Red (.245) via WinRM
  4. Verifies all 4 tasks exist
  5. Runs reboot_recovery_test.py --dry-run for final state check
  6. Logs everything to memory/mechanic/reboot-recovery.jsonl

Prereqs: pywinrm installed, WinRM enabled on remotes (already done per hosts.md).
Idempotent: safe to re-run.
"""
import json, os, sys, time, base64, subprocess, datetime, pathlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OPS_DIR = os.path.join(SCRIPT_DIR, "..", "ops")
BOOT_SCRIPT = os.path.join(OPS_DIR, "boot_recovery.py")
LOG_FILE = os.path.join(SCRIPT_DIR, "reboot-recovery.jsonl")
TASK_NAME = "FleetBootRecovery"

HOSTS = {
    "WHITE": {"ip": "127.0.0.1", "local": True},
    "PALE":  {"ip": "IP_PALE", "user": "pale",  "pw": "[REDACTED-CREDENTIAL]"},
    "BLACK": {"ip": "IP_BLACK", "user": "black", "pw": "[REDACTED-CREDENTIAL]"},
    "RED":   {"ip": "IP_RED", "user": "red",  "pw": "[REDACTED-CREDENTIAL]"},
}

REMOTE_DIR = r"C:\FleetOps"


def ts():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def log(entry):
    entry["ts"] = ts()
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"  [LOG] {entry.get('verdict', entry.get('action', ''))}")


def deploy_local():
    """Register boot task on White (local)."""
    print("[1/4] Deploying to WHITE (local)...")
    # Ensure C:\FleetOps exists and has the script
    r = subprocess.run(f'if not exist "{REMOTE_DIR}" mkdir "{REMOTE_DIR}"', shell=True, capture_output=True, text=True)
    # Copy boot_recovery.py
    dst = os.path.join(REMOTE_DIR, "boot_recovery.py")
    if os.path.exists(BOOT_SCRIPT):
        import shutil
        shutil.copy2(BOOT_SCRIPT, dst)
    else:
        log({"host": "WHITE", "verdict": "FAIL - boot_recovery.py not found at " + BOOT_SCRIPT})
        return False
    # Register schtask
    py = sys.executable.replace("python.exe", "pythonw.exe") if "python.exe" in sys.executable else sys.executable
    cmd = f'schtasks /create /tn "{TASK_NAME}" /tr "\"{py}\" \"{dst}\"" /sc onstart /ru SYSTEM /rl HIGHEST /f'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    ok = r.returncode == 0 and "SUCCESS" in r.stdout.upper()
    log({"host": "WHITE", "action": "register_schtask", "verdict": "PASS" if ok else f"FAIL: {r.stderr.strip()[:200]}"})
    return ok


def deploy_remote(name, cfg):
    """Deploy boot task to a remote host via WinRM."""
    print(f"[deploy] Deploying to {name} ({cfg['ip']})...")
    try:
        import winrm
    except ImportError:
        log({"host": name, "verdict": "FAIL - pywinrm not installed (pip install pywinrm)"})
        return False

    s = winrm.Session(
        f"http://{cfg['ip']}:5985/wsman",
        auth=(cfg["user"], cfg["pw"]),
        transport="ntlm"
    )
    # Create dir
    s.run_cmd("cmd", ["/c", f'if not exist "{REMOTE_DIR}" mkdir "{REMOTE_DIR}"'])
    # Copy script via base64
    with open(BOOT_SCRIPT, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ps = (f"$b = '{b64}'; $bytes = [Convert]::FromBase64String($b); "
          f"[IO.File]::WriteAllBytes('{REMOTE_DIR}\\boot_recovery.py', $bytes)")
    r = s.run_cmd("powershell", ["-NoProfile", "-Command", ps])
    if r.status_code != 0:
        log({"host": name, "verdict": f"FAIL - script copy error {r.status_code}"})
        return False
    # Find python
    r2 = s.run_cmd("cmd", ["/c", "where python"])
    py = r2.std_out.decode().strip().splitlines()[0].strip() if r2.std_out else "python"
    # Register schtask
    task_cmd = (f'schtasks /create /tn "{TASK_NAME}" '
                f'/tr "\"{py}\" \"{REMOTE_DIR}\\boot_recovery.py\"" '
                f'/sc onstart /ru SYSTEM /rl HIGHEST /f')
    r3 = s.run_cmd("cmd", ["/c", task_cmd])
    ok = r3.status_code == 0
    # Verify
    r4 = s.run_cmd("schtasks", ["/query", "/tn", TASK_NAME, "/fo", "LIST"])
    verified = r4.status_code == 0 and TASK_NAME in r4.std_out.decode()
    log({"host": name, "action": "register_schtask", "verdict": f"{'PASS' if ok and verified else 'FAIL'} (create={ok}, verify={verified})"})
    return ok and verified


def main():
    print(f"=== Goal 4: Boot-Recovery Deployment ({ts()}) ===\n")
    results = {}

    # 1. Local (White)
    results["WHITE"] = deploy_local()

    # 2. Remotes
    for name in ["PALE", "BLACK", "RED"]:
        cfg = HOSTS[name]
        if not cfg.get("local"):
            results[name] = deploy_remote(name, cfg)
        else:
            results[name] = False

    # 3. Summary
    passed = sum(1 for v in results.values() if v)
    verdict = f"{passed}/4 hosts registered"
    print(f"\n=== RESULT: {verdict} ===")
    for h, ok in results.items():
        print(f"  {h}: {'OK' if ok else 'FAIL'}")

    log({"type": "goal4_deployment", "results": {k: ("PASS" if v else "FAIL") for k, v in results.items()}, "verdict": verdict})

    # 4. Run dry-run test
    print("\nRunning dry-run check...")
    test_script = os.path.join(SCRIPT_DIR, "reboot_recovery_test.py")
    if os.path.exists(test_script):
        r = subprocess.run([sys.executable, test_script, "--dry-run"], capture_output=True, text=True)
        print(r.stdout)
        if r.stderr:
            print(r.stderr, file=sys.stderr)

    sys.exit(0 if passed == 4 else 1)


if __name__ == "__main__":
    main()
