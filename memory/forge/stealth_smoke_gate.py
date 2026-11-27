"""
Stealth Workflow Smoke Gate
===========================
Pre-deploy gate for the packaged SMB workflows (WF1-4).
Run before Mechanic ships to fleet hosts; also usable as a periodic health check.

Usage:
    python memory/forge/stealth_smoke_gate.py          # full gate
    python memory/forge/stealth_smoke_gate.py --quick  # selftests only, no runner import

Exit codes:
    0 = GATE PASS (all workflows healthy)
    1 = GATE FAIL (one or more checks failed)
"""
import json, sys, time, pathlib, subprocess, datetime

BASE = pathlib.Path(__file__).resolve().parent.parent / "builder" / "stealth"
REPORT = pathlib.Path(__file__).resolve().parent / "stealth-gate-report.jsonl"
MAX_WALL_SEC = 120  # per-job budget from run_stealth_jobs.py

WORKFLOWS = [
    ("wf1_ar_followup", BASE / "wf1_ar_followup.py"),
    ("wf2_weekly_report", BASE / "wf2_weekly_report.py"),
    ("wf3_reminder_pipeline", BASE / "wf3_reminder_pipeline.py"),
    ("wf4_lead_followup", BASE / "wf4_lead_followup.py"),
]
RUNNER = BASE / "run_stealth_jobs.py"

def run_selftest(name, path):
    """Run a single workflow's --selftest, return (ok, elapsed_s, output)."""
    t0 = time.time()
    try:
        r = subprocess.run(
            [sys.executable, str(path), "--selftest"],
            capture_output=True, text=True, timeout=MAX_WALL_SEC
        )
        elapsed = time.time() - t0
        ok = (r.returncode == 0)
        # Prefer stdout for detail; fall back to stderr only if stdout empty
        out = r.stdout.strip() or r.stderr.strip()
        return ok, elapsed, out
    except subprocess.TimeoutExpired:
        return False, MAX_WALL_SEC, f"TIMEOUT: exceeded {MAX_WALL_SEC}s"
    except Exception as e:
        return False, time.time() - t0, f"ERROR: {e}"

def check_runner_import():
    """Verify run_stealth_jobs.py can be imported without side effects."""
    t0 = time.time()
    try:
        r = subprocess.run(
            [sys.executable, "-c", f"import importlib.util; spec=importlib.util.spec_from_file_location('runner', r'{RUNNER}'); mod=importlib.util.module_from_spec(spec); print('IMPORT OK')"],
            capture_output=True, text=True, timeout=30
        )
        elapsed = time.time() - t0
        ok = (r.returncode == 0)
        return ok, elapsed, r.stdout.strip()
    except Exception as e:
        return False, time.time() - t0, f"ERROR: {e}"

def main():
    quick = "--quick" in sys.argv
    print("=== Stealth Workflow Smoke Gate ===")
    print(f"Time: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print(f"Mode: {'quick' if quick else 'full'}")
    print()

    results = []
    all_pass = True

    # 1. Individual workflow selftests
    for name, path in WORKFLOWS:
        exists = path.exists()
        if not exists:
            results.append({"check": name, "status": "FAIL", "detail": "script not found", "elapsed_s": 0})
            all_pass = False
            print(f"  {name}: FAIL (not found)")
            continue
        ok, elapsed, out = run_selftest(name, path)
        within_budget = elapsed < MAX_WALL_SEC
        status = "PASS" if (ok and within_budget) else "FAIL"
        detail = out.splitlines()[-1] if out else "no output"
        results.append({"check": name, "status": status, "detail": detail, "elapsed_s": round(elapsed, 2)})
        all_pass = all_pass and ok and within_budget
        print(f"  {name}: {status} ({elapsed:.1f}s) - {detail}")

    # 2. Runner import check (full mode only)
    if not quick:
        ok, elapsed, out = check_runner_import()
        status = "PASS" if ok else "FAIL"
        results.append({"check": "runner_import", "status": status, "detail": out, "elapsed_s": round(elapsed, 2)})
        all_pass = all_pass and ok
        print(f"  runner_import: {status} ({elapsed:.1f}s)")

    # 3. Verdict
    verdict = "GATE PASS" if all_pass else "GATE FAIL"
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "verdict": verdict,
        "mode": "quick" if quick else "full",
        "checks": results,
    }
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"\n  VERDICT: {verdict}")
    sys.exit(0 if all_pass else 1)

if __name__ == "__main__":
    main()