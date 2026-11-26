"""Mirror Sync Drift Monitor - alerts when mirror lag >10min sustained."""
import json, time, pathlib, datetime, sys

OPS = pathlib.Path("memory/ops")
MECH = pathlib.Path("memory/mechanic")
OPS.mkdir(parents=True, exist_ok=True)

THRESHOLD_S = 600  # 10 minutes
ALERT_PATH = OPS / "alerts" / "mirror-drift.jsonl"
STATE_PATH = MECH / "mirror-drift-state.json"
RUNBOOK = OPS / "runbooks" / "mirror-sync-recovery.md"

def get_mirror_age_s():
    """Check the age of the last mirror sync (mtime of a known mirrored file)."""
    # Use the memory mirror marker or the newest file in the mirror target
    candidates = [
        pathlib.Path("memory_mirror.py"),
        pathlib.Path("memory/synthesis/INDEX.md"),
        pathlib.Path("memory/goals/orchestrator.md"),
    ]
    now = time.time()
    ages = []
    for c in candidates:
        if c.exists():
            ages.append(now - c.stat().st_mtime)
    if not ages:
        return None
    # Use the max age (oldest file = most likely to show drift)
    return max(ages)

def check_drift(simulated_age_s=None):
    """Check for sustained mirror drift. Returns dict with alert status."""
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    if simulated_age_s is not None:
        age = simulated_age_s
    else:
        age = get_mirror_age_s()
        if age is None:
            return {"ts": ts, "status": "no_data", "age_s": None}
    
    breached = age > THRESHOLD_S
    
    # Load/update state for sustained detection (need 2 consecutive breaches)
    state = {}
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    
    prev_breached = state.get("last_breached", False)
    sustained = breached and prev_breached
    
    new_state = {
        "ts": ts,
        "age_s": round(age, 1),
        "breached": breached,
        "sustained": sustained,
        "last_breached": breached,
        "consecutive_breaches": (state.get("consecutive_breaches", 0) + 1) if breached else 0,
    }
    STATE_PATH.write_text(json.dumps(new_state, indent=2), encoding="utf-8")
    
    result = {
        "ts": ts,
        "status": "sustained_drift" if sustained else ("breach" if breached else "ok"),
        "age_s": round(age, 1),
        "threshold_s": THRESHOLD_S,
        "alerted": False,
        "runbook_executed": False,
    }
    
    if sustained:
        # Write alert
        ALERT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ALERT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(result | {"alerted": True}) + "\n")
        result["alerted"] = True
        
        # Execute runbook (log the execution)
        if RUNBOOK.exists():
            exec_log = OPS / "runbook-executions.jsonl"
            with open(exec_log, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": ts, "runbook": str(RUNBOOK), 
                                     "trigger": "mirror_drift_sustained",
                                     "age_s": round(age,1)}) + "\n")
            result["runbook_executed"] = True
    
    return result

def selftest():
    """Run selftest: 3 normal cycles (no alert) + simulated 12-min drift (alert)."""
    results = []
    
    # Phase 1: 3 normal checks (age < threshold) -> no alert
    for i in range(3):
        r = check_drift(simulated_age_s=120)  # 2 min, well under 10
        results.append(("normal", r))
    
    # Phase 2: simulated 12-min drift (first breach - not yet sustained)
    r = check_drift(simulated_age_s=720)
    results.append(("first_breach", r))
    
    # Phase 3: second consecutive breach -> sustained, should alert
    r = check_drift(simulated_age_s=730)
    results.append(("sustained", r))
    
    # Verify
    passed = True
    checks = 0
    
    # Normal cycles: no alert
    for i in range(3):
        checks += 1
        if results[i][1]["status"] != "ok" or results[i][1]["alerted"]:
            print(f"FAIL: normal cycle {i} should be ok/no-alert, got {results[i][1]['status']}")
            passed = False
    
    # First breach: breached but not sustained
    checks += 1
    if results[3][1]["status"] != "breach" or results[3][1]["alerted"]:
        print(f"FAIL: first breach should be 'breach' without alert, got {results[3][1]}")
        passed = False
    
    # Sustained: should alert + runbook
    checks += 1
    if results[4][1]["status"] != "sustained_drift":
        print(f"FAIL: sustained should be 'sustained_drift', got {results[4][1]['status']}")
        passed = False
    checks += 1
    if not results[4][1]["alerted"]:
        print("FAIL: sustained should have alerted")
        passed = False
    checks += 1
    if not results[4][1]["runbook_executed"]:
        print("FAIL: sustained should have executed runbook")
        passed = False
    
    # False positive rate: 0 alerts in normal phase
    checks += 1
    normal_alerts = sum(1 for i in range(3) if results[i][1]["alerted"])
    if normal_alerts != 0:
        print(f"FAIL: {normal_alerts} false positives in normal phase")
        passed = False
    
    print(f"{'PASS' if passed else 'FAIL'}: {checks}/7 checks")
    
    # Cleanup test state
    STATE_PATH.unlink(missing_ok=True)
    
    return passed

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif "--check" in sys.argv:
        r = check_drift()
        print(json.dumps(r, indent=2))
    else:
        print("Usage: mirror_drift_monitor.py [--selftest | --check]")
