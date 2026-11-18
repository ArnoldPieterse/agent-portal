#!/usr/bin/env python3
"""deploy_one_host.py - Register FleetBootRecovery schtask on THIS host only.

Copy this file + reboot_recover.py to the target host, then run:
    python deploy_one_host.py
(as admin or via RunAs)

Verifies: task exists + correct trigger. Logs to reboot-recovery.jsonl.
Idempotent: /f flag overwrites existing task.
"""
import json, sys, subprocess, datetime, pathlib, platform

TASK_NAME = "FleetBootRecovery"
SCRIPT_DIR = pathlib.Path(__file__).parent
RECOVER_SCRIPT = SCRIPT_DIR / "reboot_recover.py"
LOG_FILE = SCRIPT_DIR / "reboot-recovery.jsonl"
HOST = platform.node()

def main():
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    py_exe = sys.executable
    script_path = str(RECOVER_SCRIPT.resolve())
    
    if not RECOVER_SCRIPT.exists():
        print(f"FAIL: {RECOVER_SCRIPT} not found. Copy reboot_recover.py alongside this script.")
        log({"ts": ts, "host": HOST, "type": "deploy", "registered": False,
             "error": "reboot_recover.py missing"})
        sys.exit(1)
    
    # Register
    cmd = [
        "schtasks", "/create",
        "/tn", TASK_NAME,
        "/tr", f'"{py_exe}" "{script_path}" --force',
        "/sc", "onstart",
        "/ru", "SYSTEM",
        "/rl", "HIGHEST",
        "/f",
    ]
    print(f"Running: {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    ok = r.returncode == 0
    if not ok:
        print(f"FAIL: {r.stderr.strip()}")
        log({"ts": ts, "host": HOST, "type": "deploy", "registered": False,
             "error": r.stderr.strip()[:200]})
        sys.exit(1)
    
    # Verify
    v = subprocess.run(["schtasks", "/query", "/tn", TASK_NAME, "/fo", "LIST"],
                       capture_output=True, text=True)
    verified = v.returncode == 0 and TASK_NAME in v.stdout
    
    entry = {"ts": ts, "host": HOST, "type": "deploy",
             "registered": True, "verified": verified,
             "task": TASK_NAME, "trigger": "onstart", "user": "SYSTEM",
             "script": script_path}
    log(entry)
    print(f"PASS: {TASK_NAME} registered + verified on {HOST}")
    if not verified:
        print(f"  WARNING: task registered but query failed: {v.stderr.strip()[:100]}")

    # Dry-run the recovery script to confirm it works
    d = subprocess.run([py_exe, str(RECOVER_SCRIPT), "--dry-run"],
                       capture_output=True, text=True, timeout=20)
    dry_ok = d.returncode == 0
    print(f"Dry-run: {'PASS' if dry_ok else 'FAIL'}")
    if not dry_ok:
        print(f"  {d.stdout.strip()} {d.stderr.strip()[:100]}")
    
    entry["dry_run"] = dry_ok
    # Append dry_run result to log (rewrite last line)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({"ts": ts, "host": HOST, "type": "deploy_dryrun", "pass": dry_ok}) + "\n")

    print(f"\nDone. Host={HOST} task={TASK_NAME} registered={ok} verified={verified} dry_run={dry_ok}")
    sys.exit(0 if (ok and verified and dry_ok) else 1)

def log(entry):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    main()