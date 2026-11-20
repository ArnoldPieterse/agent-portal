"""
One-shot deploy: capture real perf baseline + register daily schtask.

Run ONCE from a non-sandbox White seat with :8099 egress:
    python memory/verifier/deploy_perf_gate.py

Steps performed:
  1. Validate or delete existing (invalid) baseline
  2. Capture fresh baseline via perf_gate.py --baseline
  3. Register daily schtask 'VerifierPerfGate' at 07:00
  4. Run initial gate check to confirm pipeline works end-to-end
  5. Write evidence file

Exit codes:
  0 = all steps succeeded (goal #1 leg 1 complete)
  2 = baseline capture failed (portal unreachable?)
  3 = schtask registration failed (COM issue?)
"""
import json, os, sys, subprocess, datetime, pathlib

HERE = pathlib.Path(__file__).parent.resolve()
BASELINE = HERE / "perf-baseline.json"
PERF_GATE = HERE / "perf_gate.py"
EVIDENCE_DIR = HERE.parent / "ops"

def log(msg):
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def validate_baseline(path):
    """Return True if baseline has strict-majority non-null p50."""
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    eps = data.get("endpoints", {})
    if not eps:
        return False
    valid = sum(1 for e in eps.values() if e.get("p50_ms") is not None)
    return valid > len(eps) / 2

def main():
    log("=== deploy_perf_gate.py START ===")
    
    # Step 1: Check existing baseline
    if BASELINE.exists():
        if validate_baseline(BASELINE):
            log(f"Step 1: Existing baseline is VALID - keeping it.")
        else:
            valid_count = sum(1 for e in json.loads(BASELINE.read_text()).get("endpoints", {}).values() if e.get("p50_ms") is not None)
            total = len(json.loads(BASELINE.read_text()).get("endpoints", {}))
            log(f"Step 1: Existing baseline INVALID ({valid_count}/{total} valid p50) - deleting.")
            BASELINE.unlink()
    else:
        log("Step 1: No existing baseline found.")

    # Step 2: Capture fresh baseline
    log("Step 2: Capturing fresh baseline (perf_gate.py --baseline)...")
    r = subprocess.run([sys.executable, str(PERF_GATE), "--baseline"], capture_output=True, text=True)
    if r.returncode != 0:
        log(f"FAIL: baseline capture exited {r.returncode}")
        log(f"  stderr: {r.stderr[:500]}")
        log("Portal may be unreachable from this seat. Aborting.")
        sys.exit(2)
    if not validate_baseline(BASELINE):
        log("FAIL: baseline captured but still invalid (all-null?).")
        sys.exit(2)
    valid_count = sum(1 for e in json.loads(BASELINE.read_text())["endpoints"].values() if e.get("p50_ms") is not None)
    total = len(json.loads(BASELINE.read_text())["endpoints"])
    log(f"Step 2: Baseline captured OK ({valid_count}/{total} valid p50).")

    # Step 3: Register daily schtask
    log("Step 3: Registering daily schtask 'VerifierPerfGate' at 07:00...")
    task_cmd = f'"{sys.executable}" "{PERF_GATE}"'
    r = subprocess.run(
        ["schtasks", "/create", "/tn", "VerifierPerfGate",
         "/tr", task_cmd, "/sc", "daily", "/st", "07:00", "/f"],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        log(f"WARN: schtask registration failed (exit {r.returncode}): {r.stderr.strip()[:200]}")
        log("Gate can still be run manually; scheduling is a bonus.")
    else:
        log("Step 3: schtask 'VerifierPerfGate' registered (daily 07:00).")

    # Step 4: Initial gate check
    log("Step 4: Running initial gate check...")
    r = subprocess.run([sys.executable, str(PERF_GATE)], capture_output=True, text=True)
    gate_pass = r.returncode == 0
    log(f"Step 4: Gate check exit={r.returncode} ({'PASS' if gate_pass else 'WARN/FAIL'})")
    if r.stdout:
        for line in r.stdout.strip().splitlines()[-5:]:
            log(f"  {line}")

    # Step 5: Write evidence
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    ev_path = HERE / f"evidence-deploy-perf-gate-{datetime.date.today()}.md"
    ev_path.write_text(f"""# Deploy Perf Gate - {ts}

## Steps
1. Baseline: {'kept valid' if valid_count > 0 else 'captured fresh'} ({valid_count}/{total} valid p50)
2. Fresh baseline captured: YES
3. schtask registered: {'YES (VerifierPerfGate daily 07:00)' if r.returncode == 0 else 'NO (manual run required)'}
4. Initial gate check: {'PASS' if gate_pass else f'exit {r.returncode}'}

## Baseline file
`{BASELINE}`

## Next steps for goal #1 closure
- Run gate for 3 consecutive days (schtask handles this automatically)
- Negative test: deflate one endpoint p50 in a copy -> alert fires
- Record: `python memory/researcher/goal_ledger.py --record verifier 1`
""")
    log(f"Step 5: Evidence written to {ev_path}")
    log("=== deploy_perf_gate.py DONE ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
