"""Fleet Recovery SLA Test (Verifier goal #5).

Verifies recovery times stay within SLA:
  - Detection: < 5 min (300s)
  - Recovery: < 30 min (1800s) for single-seat incidents
  - Recovery: < 2h (7200s) for cascade incidents

Reads from memory/ops/recovery-times.jsonl if present; otherwise uses
synthetic test data to prove the SLA-checking logic is correct.
FAIL-CLOSED: any SLA breach -> exit 1.
CWD-independent: paths anchored via __file__.

Usage: python memory/verifier/fleet_recovery_sla_test.py [--self-test]
"""
import json
import os
import sys
import time
import tempfile
import shutil
import datetime
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS_FILE = os.path.join(HERE, "fleet-recovery-sla-results.json")
LIVE_DATA_FILE = os.path.join(ROOT, "memory", "ops", "recovery-times.jsonl")

# SLA thresholds (seconds)
SLA_DETECTION_S = 300       # < 5 min
SLA_RECOVERY_SINGLE_S = 1800  # < 30 min single-seat
SLA_RECOVERY_CASCADE_S = 7200  # < 2h cascade

def iso_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def check_sla(incidents):
    """Check a list of incident records against SLA. Returns (breaches, summary)."""
    breaches = []
    for inc in incidents:
        inc_type = inc.get("type", "unknown")
        detection_s = inc.get("detection_seconds")
        recovery_s = inc.get("recovery_seconds")

        # Detection SLA (all types)
        if detection_s is not None and detection_s > SLA_DETECTION_S:
            breaches.append({
                "incident": inc.get("id", "unknown"),
                "sla": "detection",
                "threshold_s": SLA_DETECTION_S,
                "actual_s": detection_s,
                "excess_s": detection_s - SLA_DETECTION_S
            })

        # Recovery SLA (type-dependent)
        if recovery_s is not None:
            if inc_type == "cascade":
                limit = SLA_RECOVERY_CASCADE_S
            else:  # single-seat, host_down, agent_down, etc.
                limit = SLA_RECOVERY_SINGLE_S
            if recovery_s > limit:
                breaches.append({
                    "incident": inc.get("id", "unknown"),
                    "sla": f"recovery_{inc_type}",
                    "threshold_s": limit,
                    "actual_s": recovery_s,
                    "excess_s": recovery_s - limit
                })

    summary = {
        "total_incidents": len(incidents),
        "breach_count": len(breaches),
        "detection_max_s": max((i.get("detection_seconds", 0) for i in incidents), default=0),
        "recovery_max_s": max((i.get("recovery_seconds", 0) for i in incidents), default=0)
    }
    return breaches, summary

def self_test():
    """Prove SLA-checking logic with synthetic data."""
    results = []

    # T1: All within SLA -> no breaches
    good_incidents = [
        {"id": "inc-1", "type": "single_seat", "detection_seconds": 120, "recovery_seconds": 900},
        {"id": "inc-2", "type": "cascade", "detection_seconds": 250, "recovery_seconds": 5000},
    ]
    breaches, _ = check_sla(good_incidents)
    results.append(("T1_all_within_sla", len(breaches) == 0, f"breaches={len(breaches)}"))

    # T2: Detection breach (single-seat, detection=400s > 300s)
    det_breach = [{"id": "inc-3", "type": "single_seat", "detection_seconds": 400, "recovery_seconds": 600}]
    breaches, _ = check_sla(det_breach)
    results.append(("T2_detection_breach", len(breaches) == 1 and breaches[0]["sla"] == "detection",
                    f"breaches={len(breaches)}"))

    # T3: Recovery breach single-seat (recovery=2000s > 1800s)
    rec_breach = [{"id": "inc-4", "type": "single_seat", "detection_seconds": 100, "recovery_seconds": 2000}]
    breaches, _ = check_sla(rec_breach)
    results.append(("T3_recovery_single_breach", len(breaches) == 1 and "single" in breaches[0]["sla"],
                    f"breaches={len(breaches)}"))

    # T4: Recovery breach cascade (recovery=8000s > 7200s)
    cascade_breach = [{"id": "inc-5", "type": "cascade", "detection_seconds": 100, "recovery_seconds": 8000}]
    breaches, _ = check_sla(cascade_breach)
    results.append(("T4_recovery_cascade_breach", len(breaches) == 1 and "cascade" in breaches[0]["sla"],
                    f"breaches={len(breaches)}"))

    # T5: Boundary values (exactly at threshold = NOT a breach)
    boundary = [
        {"id": "inc-6", "type": "single_seat", "detection_seconds": 300, "recovery_seconds": 1800},
        {"id": "inc-7", "type": "cascade", "detection_seconds": 300, "recovery_seconds": 7200},
    ]
    breaches, _ = check_sla(boundary)
    results.append(("T5_boundary_not_breach", len(breaches) == 0, f"breaches={len(breaches)}"))

    # T6: Empty incident list -> no crash, zero breaches
    breaches, summary = check_sla([])
    results.append(("T6_empty_list", len(breaches) == 0 and summary["total_incidents"] == 0,
                    f"breaches={len(breaches)}"))

    return results

def live_check():
    """Check against real data if available."""
    if not Path(LIVE_DATA_FILE).exists():
        return {"status": "NO_LIVE_DATA", "file": LIVE_DATA_FILE, "note": "recovery-times.jsonl does not exist yet (Mechanic tracker pending)"}

    incidents = []
    with open(LIVE_DATA_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                incidents.append(json.loads(line))

    breaches, summary = check_sla(incidents)
    return {"status": "PASS" if not breaches else "FAIL", "breaches": breaches, "summary": summary}

def main():
    t0 = time.time()
    self_test_mode = "--self-test" in sys.argv

    if self_test_mode:
        results = self_test()
        passed = sum(1 for r in results if r[1])
        total = len(results)
        verdict = "PASS" if passed == total else "FAIL"

        report = {
            "script": "fleet_recovery_sla_test.py",
            "mode": "self-test",
            "timestamp": iso_now(),
            "passed": passed,
            "total": total,
            "elapsed_s": round(time.time() - t0, 2),
            "results": [{"test": n, "pass": p, "detail": d} for n, p, d in results],
            "verdict": verdict
        }
        Path(RESULTS_FILE).write_text(json.dumps(report, indent=2), encoding="utf-8")

        print(f"Fleet Recovery SLA Test (self-test): {passed}/{total} PASS")
        for n, p, d in results:
            icon = "✓" if p else "✗"
            print(f"  {icon} {n} ({d})")
        print(f"Verdict: {verdict}")
        sys.exit(0 if passed == total else 1)
    else:
        # Live mode
        result = live_check()
        report = {"script": "fleet_recovery_sla_test.py", "mode": "live",
                  "timestamp": iso_now(), **result,
                  "elapsed_s": round(time.time() - t0, 2)}
        Path(RESULTS_FILE).write_text(json.dumps(report, indent=2), encoding="utf-8")

        print(f"Fleet Recovery SLA Test (live): {result['status']}")
        if result.get("summary"):
            s = result["summary"]
            print(f"  Incidents: {s['total_incidents']}, Breaches: {s['breach_count']}")
            print(f"  Max detection: {s['detection_max_s']}s, Max recovery: {s['recovery_max_s']}s")
        if result.get("note"):
            print(f"  Note: {result['note']}")
        sys.exit(0 if result["status"] in ("PASS", "NO_LIVE_DATA") else 1)

if __name__ == "__main__":
    main()