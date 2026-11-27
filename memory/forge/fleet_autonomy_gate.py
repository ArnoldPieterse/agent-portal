"""
fleet_autonomy_gate.py - Unified Fleet Autonomy Gate
Forge, 2026-11-26

Single entry point that runs ALL Forge gates in sequence and produces one
verdict for the fleet's autonomy-readiness:

  1. runbook_audit.py       - all ops runbooks have executable companions
  2. consistency_check.py   - all hosts report same model+config
  3. drift_detect.py        - no silent dep/test drift in pipeline
  4. stealth_smoke_gate.py  - WF1-3 selftest pass

Usage: python memory/forge/fleet_autonomy_gate.py [--json] [--skip <n>]
       --skip 1,3  (skip gate numbers)
Exit:  0 = ALL GATES PASS (fleet autonomy ready)
       1 = ONE OR MORE GATES FAILED
       2 = SCRIPT ERROR (gate couldn't run at all)

Round topic: Fleet Autonomy Convergence - this is the convergence point.
"""
import sys, subprocess, json, time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(".")
GATES = [
    {
        "id": 1,
        "name": "runbook_audit",
        "cmd": [sys.executable, str(ROOT / "memory/forge/runbook_audit.py"), "--json"],
        "pass_check": lambda r: r.returncode == 0,
        "desc": "All ops runbooks have executable companion scripts",
    },
    {
        "id": 2,
        "name": "consistency_check",
        "cmd": [sys.executable, str(ROOT / "memory/forge/consistency_check.py")],
        "pass_check": lambda r: "VERDICT: PASS" in (r.stdout or ""),
        "desc": "All hosts report same model version + config hash",
    },
    {
        "id": 3,
        "name": "drift_detect",
        "cmd": [sys.executable, str(ROOT / "memory/forge/drift_detect.py")],
        "pass_check": lambda r: "VERDICT: CLEAN" in (r.stdout or ""),
        "desc": "No silent dep/test drift in gate pipeline",
    },
    {
        "id": 4,
        "name": "stealth_smoke_gate",
        "cmd": [sys.executable, str(ROOT / "memory/forge/stealth_smoke_gate.py")],
        "pass_check": lambda r: r.returncode == 0,
        "desc": "WF1-3 selftest pass (pre-deploy smoke)",
    },
]

def parse_skip(arg_val: str) -> set[int]:
    """Parse --skip value like '1,3' into a set of gate IDs to skip."""
    return {int(x.strip()) for x in arg_val.split(",") if x.strip()}

def main():
    output_json = "--json" in sys.argv
    skip_ids: set[int] = set()
    
    # Parse --skip
    if "--skip" in sys.argv:
        idx = sys.argv.index("--skip")
        if idx + 1 < len(sys.argv):
            skip_ids = parse_skip(sys.argv[idx + 1])
    
    results = []
    overall_start = time.monotonic()
    
    for gate in GATES:
        if gate["id"] in skip_ids:
            results.append({
                "gate": gate["id"],
                "name": gate["name"],
                "status": "SKIPPED",
                "duration_s": 0.0,
                "detail": "skipped by --skip",
            })
            continue
        
        g_start = time.monotonic()
        try:
            r = subprocess.run(
                gate["cmd"],
                capture_output=True, text=True, timeout=180,
                cwd=str(ROOT),
            )
            duration = round(time.monotonic() - g_start, 2)
            passed = gate["pass_check"](r)
            status = "PASS" if passed else "FAIL"
            
            # Extract key lines for detail
            stdout_lines = (r.stdout or "").strip().splitlines()
            stderr_lines = (r.stderr or "").strip().splitlines()
            # Keep last 3 meaningful lines from stdout + first 2 from stderr
            detail_parts = stdout_lines[-3:] if stdout_lines else []
            if stderr_lines:
                detail_parts += [f"STDERR: {l}" for l in stderr_lines[:2]]
            
            results.append({
                "gate": gate["id"],
                "name": gate["name"],
                "status": status,
                "duration_s": duration,
                "exit_code": r.returncode,
                "detail": " | ".join(detail_parts)[:300],
            })
        except subprocess.TimeoutExpired:
            duration = round(time.monotonic() - g_start, 2)
            results.append({
                "gate": gate["id"],
                "name": gate["name"],
                "status": "FAIL",
                "duration_s": duration,
                "exit_code": -1,
                "detail": "TIMEOUT (>180s)",
            })
        except Exception as e:
            duration = round(time.monotonic() - g_start, 2)
            results.append({
                "gate": gate["id"],
                "name": gate["name"],
                "status": "ERROR",
                "duration_s": duration,
                "exit_code": -1,
                "detail": str(e)[:200],
            })
    
    total_time = round(time.monotonic() - overall_start, 2)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
    skipped = sum(1 for r in results if r["status"] == "SKIPPED")
    
    verdict = "FLEET AUTONOMY READY" if failed == 0 else "GATE FAILURE - NOT READY"
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "total_time_s": total_time,
        "gates_passed": passed,
        "gates_failed": failed,
        "gates_skipped": skipped,
        "results": results,
    }
    
    if output_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"=== Fleet Autonomy Gate ===")
        print(f"Time: {report['timestamp']}")
        print()
        for r in results:
            icon = {"PASS": "+", "FAIL": "X", "ERROR": "!", "SKIPPED": "-"}[r["status"]]
            dur = f"{r['duration_s']:.1f}s" if r["duration_s"] else "  -"
            print(f"  [{icon}] Gate {r['gate']} ({r['name']}): {r['status']} {dur}")
            if r["detail"] and r["status"] != "PASS":
                print(f"      {r['detail'][:120]}")
        print()
        print(f"  Total: {passed} PASS / {failed} FAIL / {skipped} SKIP ({total_time}s)")
        print(f"  VERDICT: {verdict}")
    
    # Append to report log
    log_path = ROOT / "memory/forge/fleet-autonomy-gate-report.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(report) + "\n")
    
    exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
