#!/usr/bin/env python3
"""preflight_check.py - Validate ALL prerequisites for unblock_all.py BEFORE running it.

Run from the same seat you plan to run unblock_all.py:
    python memory/mechanic/preflight_check.py [--host black]

Checks (each independent, all must PASS for GO):
  P1: Portal listening on :8099 (needed for CB live verification)
  P2: WinRM port 5985 reachable to target host (needed for E2E test)
  P3: deploy_all_schtasks.py exists + py_compile clean
  P4: winrm_e2e_test.py exists + py_compile clean
  P5: unblock_all.py exists + py_compile clean
  P6: mirror_heal.py exists (canonical module for Goal 2)
  P7: load_trend.jsonl exists + has >= 1 data row (Goal 1 partial data)

Exit code: 0 = ALL PASS (safe to run unblock_all.py), 1 = one or more FAIL
Output: structured JSON to stdout + human-readable summary
"""
import json, os, socket, subprocess, sys, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent   # memory/mechanic/
ROOT = HERE.parent.parent                 # project root

def check(name, desc):
    """Run a check, return (name, pass/fail, detail)."""
    try:
        ok, detail = desc()
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {detail}")
        return {"check": name, "status": status, "detail": detail}
    except Exception as e:
        print(f"  [FAIL] {name}: exception {type(e).__name__}: {e}")
        return {"check": name, "status": "FAIL", "detail": f"{type(e).__name__}: {e}"}

def p1_portal():
    """Portal on :8099."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect(("127.0.0.1", 8099))
        return True, "port 8099 open"
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        return False, f"port 8099 closed ({e})"
    finally:
        s.close()

def p2_winrm(host):
    """WinRM 5985 reachable to target."""
    # Resolve host name from agents.json or use IP
    hosts = {"black": "IP_LAN", "pale": "IP_LAN", "red": "IP_LAN"}
    ip = hosts.get(host.lower(), host)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((ip, 5985))
        return True, f"{host} ({ip}):5985 reachable"
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        return False, f"{host} ({ip}):5985 unreachable ({e})"
    finally:
        s.close()

def _script_exists(rel_path):
    p = ROOT / rel_path
    if not p.exists():
        return False, f"missing: {rel_path}"
    # py_compile check
    r = subprocess.run([sys.executable, "-m", "py_compile", str(p)],
                       capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        return False, f"py_compile FAIL: {r.stderr[:200]}"
    return True, f"{rel_path} exists + compiles"

def p3_deploy_schtasks():
    return _script_exists("memory/mechanic/deploy_all_schtasks.py")

def p4_winrm_e2e():
    return _script_exists("memory/mechanic/e2e_anti_stall_test.py")

def p5_unblock_all():
    return _script_exists("memory/mechanic/unblock_all.py")

def p6_mirror_heal():
    return _script_exists("memory/ops/mirror_heal.py")

def p7_load_trend():
    p = ROOT / "memory" / "ops" / "loadtest" / "load_trend.jsonl"
    if not p.exists():
        # Try alternate location
        alt = ROOT / "memory" / "mechanic" / "load_trend.jsonl"
        if alt.exists():
            p = alt
        else:
            return False, "load_trend.jsonl not found in expected locations"
    lines = [l for l in p.read_text().splitlines() if l.strip()]
    if len(lines) == 0:
        return False, "load_trend.jsonl exists but empty (0 rows)"
    return True, f"load_trend.jsonl has {len(lines)} data row(s)"

def main():
    host = "black"
    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        if idx + 1 < len(sys.argv):
            host = sys.argv[idx + 1]

    ts = datetime.datetime.now().isoformat()
    print(f"=== preflight_check.py === {ts}")
    print(f"Target WinRM host: {host}\n")

    results = []
    results.append(check("P1_portal_8099", p1_portal))
    results.append(check("P2_winrm_" + host, lambda: p2_winrm(host)))
    results.append(check("P3_deploy_schtasks", p3_deploy_schtasks))
    results.append(check("P4_winrm_e2e_test", p4_winrm_e2e))
    results.append(check("P5_unblock_all", p5_unblock_all))
    results.append(check("P6_mirror_heal", p6_mirror_heal))
    results.append(check("P7_load_trend_data", p7_load_trend))

    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    verdict = "GO" if passed == total else f"HOLD ({total - passed} failing)"

    print(f"\n=== VERDICT: {verdict} ({passed}/{total} pass) ===")
    
    # Write JSON evidence
    evidence = {
        "ts": ts,
        "host": host,
        "results": results,
        "verdict": verdict,
        "passed": passed,
        "total": total
    }
    out_file = HERE / f"preflight-{datetime.date.today()}.jsonl"
    with open(out_file, "a") as f:
        f.write(json.dumps(evidence) + "\n")
    print(f"Evidence: {out_file.relative_to(ROOT)}")

    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
