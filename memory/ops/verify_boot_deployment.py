#!/usr/bin/env python3
"""verify_boot_deployment.py - Post-deployment check for FleetBootRecovery.

Run on each fleet host (locally or via RDP) to confirm boot-recovery is wired:
    python verify_boot_deployment.py

Checks (no admin required for read-only verification):
  1. boot_recovery.py exists at expected path
  2. fleet_reload.py exists at expected path
  3. Python executable on PATH is valid
  4. FleetBootRecovery schtask exists (via python subprocess; falls back to file check if COM broken)

Exit codes: 0 = all pass, 1 = one or more checks failed.
"""
import os, sys, platform, json, datetime, subprocess

HOSTNAME = platform.node()
OPS_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_NAME = "FleetBootRecovery"

def check_file(path, label):
    ok = os.path.isfile(path)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {path}")
    return ok

def check_python():
    exe = sys.executable
    ok = os.path.isfile(exe)
    ver = platform.python_version()
    print(f"  [{'PASS' if ok else 'FAIL'}] Python: {exe} ({ver})")
    return ok

def check_schtasks():
    """Try schtasks /query; if COM is broken, fall back to checking the task XML."""
    try:
        r = subprocess.run(
            ["schtasks", "/query", "/tn", TASK_NAME, "/fo", "CSV"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            print(f"  [PASS] schtask {TASK_NAME} exists")
            return True
        else:
            # COM might be broken; try XML file check
            task_xml = rf"C:\Windows\System32\Tasks\{TASK_NAME}"
            ok = os.path.isfile(task_xml)
            print(f"  [{'PASS' if ok else 'FAIL'}] schtask {TASK_NAME} (XML fallback: {task_xml})")
            return ok
    except Exception as e:
        # COM broken or timeout - try XML
        task_xml = rf"C:\Windows\System32\Tasks\{TASK_NAME}"
        ok = os.path.isfile(task_xml)
        print(f"  [{'PASS' if ok else 'FAIL'}] schtask {TASK_NAME} (XML fallback, COM error: {e})")
        return ok

def main():
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n=== Boot-Recovery Deployment Check: {HOSTNAME} ({ts}) ===")
    
    results = []
    results.append(check_file(os.path.join(OPS_DIR, "boot_recovery.py"), "boot script"))
    results.append(check_file(os.path.join(OPS_DIR, "fleet_reload.py"), "reload script"))
    results.append(check_python())
    results.append(check_schtasks())
    
    passed = sum(results)
    total = len(results)
    status = "READY" if passed == total else f"INCOMPLETE ({passed}/{total})"
    print(f"\n  Verdict: {status}")
    
    # Write structured result
    evidence_dir = os.path.join(OPS_DIR, "..", "mechanic")
    log_path = os.path.join(evidence_dir, "boot-deploy-verify.jsonl")
    entry = {
        "ts": ts,
        "host": HOSTNAME,
        "checks": {"boot_script": results[0], "reload_script": results[1],
                   "python": results[2], "schtask": results[3]},
        "verdict": status
    }
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"  Logged: {log_path}")
    except Exception:
        pass
    
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()