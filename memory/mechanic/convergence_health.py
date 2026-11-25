"""Convergence Infra Health Check.

Weekly check: verify seat-matrix fresh, autonomy-score updated, intervention log growing, cycle estimator running.
Output: memory/ops/convergence-health.json (pass/fail per check).

Usage:
  python memory/mechanic/convergence_health.py          # live check
  python memory/mechanic/convergence_health.py --selftest  # simulated
"""
import json, pathlib, datetime, sys, os

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
OUTPUT = BASE / "memory" / "ops" / "convergence-health.json"

# Max age (hours) before a file is considered stale
STALE_HOURS = 48  # weekly check: anything >2 days old is suspect

def file_age_hours(path):
    """Return hours since last modification, or None if missing."""
    p = pathlib.Path(path)
    if not p.exists():
        return None
    mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime)
    return (datetime.datetime.now() - mtime).total_seconds() / 3600.0

def file_line_count(path):
    """Return line count of a file, or 0 if missing."""
    p = pathlib.Path(path)
    if not p.exists():
        return 0
    with open(p, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)

def cycle_estimate_age_hours():
    """Hours since the last cycle_estimate write, or None if absent.

    The estimator (builder/orchestrator) does NOT write a standalone file; it
    merges a 'cycle_estimate' block + 'cycle_estimate_ts' into fleet-mode.json.
    """
    fm = BASE / "memory" / "ops" / "fleet-mode.json"
    if not fm.exists():
        return None
    try:
        data = json.loads(fm.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    ts = data.get("cycle_estimate_ts")
    if not ts or "cycle_estimate" not in data:
        return None
    try:
        dt = datetime.datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        age = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds() / 3600.0
        return max(0.0, age)
    except ValueError:
        return None

def run_check(overrides=None):
    """Run health checks. overrides dict can inject file paths/ages for testing."""
    ov = overrides or {}
    results = []

    # Check 1: seat-matrix.json fresh
    sm_path = ov.get("seat_matrix", BASE / "memory" / "ops" / "seat-matrix.json")
    age = ov.get("seat_matrix_age_hours", file_age_hours(sm_path))
    if age is None:
        results.append({"check": "seat_matrix_fresh", "status": "FAIL", "detail": "file missing"})
    elif age > STALE_HOURS:
        results.append({"check": "seat_matrix_fresh", "status": "FAIL", "detail": f"stale ({age:.1f}h old)"})
    else:
        results.append({"check": "seat_matrix_fresh", "status": "PASS", "detail": f"{age:.1f}h old"})

    # Check 2: autonomy-score.json updated
    as_path = ov.get("autonomy_score", BASE / "memory" / "ops" / "autonomy-score.json")
    age = ov.get("autonomy_score_age_hours", file_age_hours(as_path))
    if age is None:
        results.append({"check": "autonomy_score_updated", "status": "FAIL", "detail": "file missing"})
    elif age > STALE_HOURS:
        results.append({"check": "autonomy_score_updated", "status": "FAIL", "detail": f"stale ({age:.1f}h old)"})
    else:
        results.append({"check": "autonomy_score_updated", "status": "PASS", "detail": f"{age:.1f}h old"})

    # Check 3: intervention log growing (has >=1 line)
    il_path = ov.get("intervention_log", BASE / "memory" / "ops" / "human-interventions.jsonl")
    lines = ov.get("intervention_log_lines", file_line_count(il_path))
    if lines == 0:
        results.append({"check": "intervention_log_growing", "status": "FAIL", "detail": "no entries yet"})
    else:
        results.append({"check": "intervention_log_growing", "status": "PASS", "detail": f"{lines} entries"})

    # Check 4: cycle estimator output fresh (estimator writes cycle_estimate into fleet-mode.json)
    age = ov.get("cycle_estimator_age_hours", cycle_estimate_age_hours())
    if age is None:
        results.append({"check": "cycle_estimator_running", "status": "FAIL", "detail": "output missing"})
    elif age > STALE_HOURS * 7:  # estimator runs less frequently, allow 2 weeks
        results.append({"check": "cycle_estimator_running", "status": "FAIL", "detail": f"stale ({age:.1f}h old)"})
    else:
        results.append({"check": "cycle_estimator_running", "status": "PASS", "detail": f"{age:.1f}h old"})

    overall = "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL"
    return {
        "generated": datetime.datetime.now().isoformat(),
        "overall": overall,
        "checks": results,
    }

def selftest():
    """Verify: healthy=all PASS; simulated staleness detected."""
    errors = []

    # Test 1: all healthy -> all PASS
    healthy = run_check(overrides={
        "seat_matrix_age_hours": 2.0,
        "autonomy_score_age_hours": 5.0,
        "intervention_log_lines": 7,
        "cycle_estimator_age_hours": 24.0,
    })
    if healthy["overall"] != "PASS":
        errors.append(f"Healthy check: expected PASS, got {healthy['overall']}")
    for c in healthy["checks"]:
        if c["status"] != "PASS":
            errors.append(f"Healthy {c['check']}: expected PASS, got {c['status']}")

    # Test 2: stale seat matrix -> FAIL
    stale = run_check(overrides={
        "seat_matrix_age_hours": 72.0,  # >48h
        "autonomy_score_age_hours": 5.0,
        "intervention_log_lines": 7,
        "cycle_estimator_age_hours": 24.0,
    })
    sm_check = next(c for c in stale["checks"] if c["check"] == "seat_matrix_fresh")
    if sm_check["status"] != "FAIL":
        errors.append(f"Stale seat matrix: expected FAIL, got {sm_check['status']}")
    if stale["overall"] != "FAIL":
        errors.append(f"Stale overall: expected FAIL, got {stale['overall']}")

    # Test 3: missing file -> FAIL
    missing = run_check(overrides={
        "seat_matrix_age_hours": None,
        "autonomy_score_age_hours": 5.0,
        "intervention_log_lines": 7,
        "cycle_estimator_age_hours": 24.0,
    })
    sm_check = next(c for c in missing["checks"] if c["check"] == "seat_matrix_fresh")
    if sm_check["status"] != "FAIL":
        errors.append(f"Missing seat matrix: expected FAIL, got {sm_check['status']}")

    # Test 4: empty intervention log -> FAIL
    empty_il = run_check(overrides={
        "seat_matrix_age_hours": 2.0,
        "autonomy_score_age_hours": 5.0,
        "intervention_log_lines": 0,
        "cycle_estimator_age_hours": 24.0,
    })
    il_check = next(c for c in empty_il["checks"] if c["check"] == "intervention_log_growing")
    if il_check["status"] != "FAIL":
        errors.append(f"Empty intervention log: expected FAIL, got {il_check['status']}")

    # Test 5: stale cycle estimator (>14 days) -> FAIL
    stale_ce = run_check(overrides={
        "seat_matrix_age_hours": 2.0,
        "autonomy_score_age_hours": 5.0,
        "intervention_log_lines": 7,
        "cycle_estimator_age_hours": 400.0,  # >168h
    })
    ce_check = next(c for c in stale_ce["checks"] if c["check"] == "cycle_estimator_running")
    if ce_check["status"] != "FAIL":
        errors.append(f"Stale cycle estimator: expected FAIL, got {ce_check['status']}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return False
    else:
        print("PASS: all 5 selftest checks OK")
        print(f"  healthy=PASS, stale_sm=FAIL, missing=FAIL, empty_il=FAIL, stale_ce=FAIL")
        return True

def main():
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)

    result = run_check()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {OUTPUT}: overall={result['overall']}")
    for c in result["checks"]:
        print(f"  {c['check']}: {c['status']} ({c['detail']})")

if __name__ == "__main__":
    main()
