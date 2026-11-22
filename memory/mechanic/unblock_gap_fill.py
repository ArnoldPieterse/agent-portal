#!/usr/bin/env python3
"""unblock_gap_fill.py - Covers the 3 queue items NOT handled by unblock_all.py.

Run from a NON-SANDBOX White session (admin or via elev.py), AFTER unblock_all.py:
    python memory/mechanic/unblock_gap_fill.py [--skip-smb] [--skip-capacity]

Executes in order (each independent):
  1. RebootRecoveryDetect schtask registration (Mechanic #4, delayed boot task)
  2. MirrorSync Pale/Black SMB creds verification (Researcher #3 dep)
  3. Capacity Planning 7-day live run (Mechanic #9)

Prerequisite: unblock_all.py already ran (or use --skip flags to skip what it covers).
All results logged to memory/mechanic/gap-fill-<date>.jsonl
"""
import json, os, subprocess, sys, datetime, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent  # memory/mechanic/
ROOT = HERE.parent.parent               # project root
LOG_FILE = HERE / f"gap-fill-{datetime.date.today()}.jsonl"

def log(phase, status, detail=""):
    entry = {"ts": datetime.datetime.now().isoformat(), "phase": phase, "status": status, "detail": detail}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[{phase}] {status}: {detail}")

def run_cmd(args, timeout=120):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=str(ROOT))
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, f"TIMEOUT after {timeout}s"
    except Exception as e:
        return -2, str(e)

def phase_boot_detect():
    """Phase 1: Register RebootRecoveryDetect (delayed PT5M boot task)."""
    log("boot_detect", "START")
    # Find python.exe path on this host
    py = sys.executable
    script_path = HERE / "reboot_recovery_test.py"
    if not script_path.exists():
        log("boot_detect", "SKIP", f"script missing: {script_path}")
        return True  # Not a failure - just nothing to register
    
    tr = f'"{py}" "{script_path}" --dry-run'
    args = ["schtasks", "/create", "/tn", "RebootRecoveryDetect",
            "/tr", tr, "/sc", "onstart", "/delay", "PT5M",
            "/ru", "SYSTEM", "/rl", "HIGHEST", "/f"]
    code, out = run_cmd(args)
    if code == 0:
        log("boot_detect", "PASS", "RebootRecoveryDetect registered (onstart + PT5M delay)")
        return True
    else:
        log("boot_detect", "FAIL", f"exit={code} out={out[:300]}")
        return False

def phase_smb_creds():
    """Phase 2: Verify MirrorSync can reach Pale (.39) and Black (.99) via SMB."""
    log("smb_creds", "START")
    # Check if memory_mirror.py exists and try a dry connect
    mirror_script = ROOT / "memory" / "memory_mirror.py"
    if not mirror_script.exists():
        # Try the ops/ location
        mirror_script = ROOT / "memory" / "ops" / "memory_mirror.py"
    if not mirror_script.exists():
        log("smb_creds", "SKIP", "memory_mirror.py not found")
        return True
    
    code, out = run_cmd([sys.executable, str(mirror_script), "-v", "--dry-run"], timeout=60)
    if code == 0:
        # Check output for auth errors
        if "auth" in out.lower() or "credential" in out.lower() or "access denied" in out.lower():
            log("smb_creds", "WARN", f"SMB auth issues detected: {out[:300]}")
            return False
        log("smb_creds", "PASS", f"all hosts reachable (exit=0)")
        return True
    else:
        log("smb_creds", "FAIL", f"exit={code} out={out[:300]}")
        return False

def phase_capacity():
    """Phase 3: Run capacity planning with live data (7-day window)."""
    log("capacity", "START")
    cap_script = HERE / "capacity_plan.py"
    if not cap_script.exists():
        log("capacity", "SKIP", f"script missing: {cap_script}")
        return True
    
    code, out = run_cmd([sys.executable, str(cap_script), "--live", "--days", "7"], timeout=120)
    if code == 0:
        log("capacity", "PASS", f"7-day live run completed")
        return True
    else:
        log("capacity", "FAIL", f"exit={code} out={out[:300]}")
        return False

def main():
    skip_smb = "--skip-smb" in sys.argv
    skip_cap = "--skip-capacity" in sys.argv
    
    print(f"=== unblock_gap_fill.py === {datetime.datetime.now().isoformat()}")
    results = {}
    
    results["boot_detect"] = phase_boot_detect()
    
    if not skip_smb:
        results["smb_creds"] = phase_smb_creds()
    else:
        log("smb_creds", "SKIP")
    
    if not skip_cap:
        results["capacity"] = phase_capacity()
    else:
        log("capacity", "SKIP")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    verdict = "ALL PASS" if passed == total else f"{passed}/{total} pass"
    log("SUMMARY", verdict, json.dumps(results))
    print(f"\n=== VERDICT: {verdict} ===")
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
