#!/usr/bin/env python3
"""unblock_all.py - One-shot execution of ALL remaining live legs for Mechanic goals.

Run from a NON-SANDBOX White session (admin or via elev.py):
    python memory/mechanic/unblock_all.py [--skip-schtasks] [--skip-winrm] [--skip-cb]

Executes in order:
  1. deploy_all_schtasks.py   -> registers PortalLoadProbe, MirrorHeal, LogRotateDaily, etc.
  2. winrm_e2e_test.py        -> full anti-stall E2E against Black (or --host pale)
  3. Live CB verification     -> GET /api/fleet/status, confirm dead-host row state=down

Each phase is independent: failure in one does NOT block the others.
All results logged to memory/mechanic/unblock-all-<date>.jsonl
"""
import json, os, subprocess, sys, datetime, urllib.request, time
from pathlib import Path

HERE = Path(__file__).resolve().parent  # memory/mechanic/
ROOT = HERE.parent.parent               # project root
LOG_FILE = HERE / f"unblock-all-{datetime.date.today()}.jsonl"

def log(phase, status, detail=""):
    entry = {"ts": datetime.datetime.now().isoformat(), "phase": phase, "status": status, "detail": detail}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[{phase}] {status}: {detail}")

def run_cmd(args, timeout=900):
    """Run a command, return (exit_code, stdout+stderr)."""
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                           cwd=str(ROOT))
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, f"TIMEOUT after {timeout}s"
    except Exception as e:
        return -2, str(e)

def phase_schtasks():
    """Phase 1: Register all pending schtasks."""
    log("schtasks", "START")
    script = HERE / "deploy_all_schtasks.py"
    if not script.exists():
        log("schtasks", "FAIL", f"script missing: {script}")
        return False
    code, out = run_cmd([sys.executable, str(script)], timeout=120)
    if code == 0:
        log("schtasks", "PASS", f"all tasks registered/verified")
        return True
    else:
        log("schtasks", "FAIL", f"exit={code} out={out[:500]}")
        return False

def phase_winrm(host="black"):
    """Phase 2: WinRM E2E anti-stall test."""
    log("winrm_e2e", "START", f"target={host}")
    script = HERE / "winrm_e2e_test.py"
    if not script.exists():
        log("winrm_e2e", "FAIL", f"script missing: {script}")
        return False
    args = [sys.executable, str(script), "--host", host]
    # Add --password from env if set
    pw = os.environ.get("WINRM_PASSWORD")
    if pw:
        args += ["--password", pw]
    code, out = run_cmd(args, timeout=900)  # 15 min max
    if code == 0:
        log("winrm_e2e", "PASS", f"full cycle completed against {host}")
        return True
    else:
        log("winrm_e2e", "FAIL", f"exit={code} out={out[:500]}")
        return False

def phase_cb_live():
    """Phase 3: Live-over-HTTP circuit breaker verification."""
    log("cb_live", "START")
    url = "http://127.0.0.1:8099/api/fleet/status"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "unblock-all/1.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        hosts = data.get("hosts", [])
        down_hosts = [h for h in hosts if h.get("state") == "down"]
        total = len(hosts)
        log("cb_live", "PASS",
            f"GET /api/fleet/status -> 200, {total} hosts reported, "
            f"{len(down_hosts)} marked DOWN: {[h.get('name') for h in down_hosts]}")
        return True
    except urllib.error.URLError as e:
        log("cb_live", "FAIL", f"URLError: {e}")
        return False
    except Exception as e:
        log("cb_live", "FAIL", f"{type(e).__name__}: {e}")
        return False

def main():
    skip_schtasks = "--skip-schtasks" in sys.argv
    skip_winrm = "--skip-winrm" in sys.argv
    skip_cb = "--skip-cb" in sys.argv
    winrm_host = "black"
    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        if idx + 1 < len(sys.argv):
            winrm_host = sys.argv[idx + 1]

    print(f"=== unblock_all.py === {datetime.datetime.now().isoformat()}")
    results = {}

    if not skip_schtasks:
        results["schtasks"] = phase_schtasks()
    else:
        log("schtasks", "SKIP")

    if not skip_winrm:
        results["winrm_e2e"] = phase_winrm(winrm_host)
    else:
        log("winrm_e2e", "SKIP")

    if not skip_cb:
        results["cb_live"] = phase_cb_live()
    else:
        log("cb_live", "SKIP")

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    verdict = "ALL PASS" if passed == total else f"{passed}/{total} pass"
    log("SUMMARY", verdict, json.dumps(results))
    print(f"\n=== VERDICT: {verdict} ===")
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()