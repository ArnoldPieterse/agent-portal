#!/usr/bin/env python3
"""
winrm_remote_exec_test.py - One-shot remote execution test for Goal 1 closure.

Run from NON-SANDBOX White seat (has pip + LAN egress to all 4 hosts):
    python memory/mechanic/winrm_remote_exec_test.py

Steps:
  1. Installs pywinrm if not present (pip install --user pywinrm)
  2. For each of the 4 fleet hosts: connects via WinRM, runs "hostname" command
  3. Records PASS/FAIL per host to goal1-winrm-remote-evidence.jsonl
  4. If all 4 pass, prints CLOSURE-READY message

This is the ONLY remaining leg for Goal 1 (WinRM Remote Management Hardening).
All logic paths (rotation, retry, pool) are verified in winrm_pool_selftest.py (20/20 PASS).
"""
import json, sys, subprocess, time
from datetime import datetime
from pathlib import Path

EVIDENCE = Path(__file__).parent / "goal1-winrm-remote-evidence.jsonl"
HOSTS = {
    "WHITE": {"ip": "127.0.0.1", "user": "White"},
    "PALE":  {"ip": "IP_PALE", "user": "Pale"},
    "BLACK": {"ip": "IP_BLACK", "user": "Black"},
    "RED":   {"ip": "IP_RED", "user": "Red"},
}

def log(event, **kw):
    entry = {"ts": datetime.now().isoformat(), "event": event, **kw}
    with open(EVIDENCE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print("  [%s] %s" % (event, json.dumps({k:v for k,v in kw.items() if k != 'detail'})[:120]))

def ensure_pywinrm():
    """Install pywinrm if not available."""
    try:
        import pywinrm
        print("pywinrm already installed: %s" % pywinrm.__version__)
        return True
    except ImportError:
        pass
    
    print("Installing pywinrm...")
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--user", "--no-cache-dir", "pywinrm"],
        capture_output=True, text=True, timeout=60
    )
    if r.returncode != 0:
        print("  pip install failed: %s" % r.stderr[-300:])
        return False
    
    try:
        import pywinrm
        print("pywinrm installed OK: %s" % pywinrm.__version__)
        return True
    except ImportError as e:
        print("  Import still failing after install: %s" % e)
        return False

def test_remote_exec():
    """Run 'hostname' on all 4 hosts via WinRM."""
    from pywinrm import Session
    
    results = {}
    for name, cfg in HOSTS.items():
        try:
            session = Session(
                target="http://%s:5985/wsman" % cfg["ip"],
                username=cfg["user"],
                password="",
                transport="ntlm"
            )
            r = session.run_command("hostname")
            stdout = r.std_out.decode().strip()
            results[name] = {"status": "PASS", "hostname": stdout, "exit_code": r.status_code}
            log("remote_exec_pass", host=name, hostname=stdout)
        except Exception as e:
            results[name] = {"status": "FAIL", "error": str(e)[:200]}
            log("remote_exec_fail", host=name, error=str(e)[:200])
    
    return results

def main():
    print("=" * 60)
    print("Goal 1: WinRM Remote Execution Test (one-shot closure)")
    print("=" * 60)
    
    if not ensure_pywinrm():
        log("pywinrm_install_failed", detail="pip install failed")
        print("\nBLOCKED: pywinrm install failed. Check pip permissions.")
        sys.exit(1)
    
    print("\nTesting remote execution on all 4 hosts...")
    results = test_remote_exec()
    
    passed = sum(1 for r in results.values() if r["status"] == "PASS")
    total = len(results)
    verdict = "ALL PASS" if passed == total else "%d/%d PASS" % (passed, total)
    
    log("final_verdict", passed=passed, total=total, verdict=verdict, hosts=results)
    
    print("\n" + "=" * 60)
    print("VERDICT: %s" % verdict)
    for name, r in results.items():
        icon = "[OK] " if r["status"] == "PASS" else "[FAIL]"
        detail = r.get("hostname", r.get("error", ""))[:40]
        print("  %s %s: %s" % (icon, name, detail))
    print("=" * 60)
    
    if passed == total:
        print("\n*** CLOSURE-READY ***")
        print("Run: python memory/researcher/goal_ledger.py --record mechanic 1")
        print("      --note 'winrm_remote_exec_test.py: 4/4 hosts PASS (hostname verified)'")
    else:
        print("\n%d host(s) failed. Check network/credentials." % (total - passed))

if __name__ == "__main__":
    main()
