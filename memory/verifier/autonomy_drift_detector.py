#!/usr/bin/env python3
"""Autonomy Score Drift Detector (Verifier Goal #4).

Monitors autonomy score over time; flags:
  - REGRESSION: drop > 10 points in a single cycle
  - STAGNATION: score plateaus (within +/-1) for 3+ consecutive cycles

Self-test: python memory/verifier/autonomy_drift_detector.py --self-test
Live:      python memory/verifier/autonomy_drift_detector.py
"""
import json, sys, os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCORE_FILE = REPO_ROOT / "memory" / "ops" / "autonomy-score.json"
HISTORY_FILE = REPO_ROOT / "memory" / "verifier" / "autonomy-score-history.jsonl"
ALERTS_FILE = REPO_ROOT / "memory" / "ops" / "alerts.jsonl"

DROP_THRESHOLD = 10.0    # points drop in single cycle (strict >)
PLATEAU_TOL = 1.0        # +/- tolerance per step for plateau
PLATEAU_CYCLES = 3       # consecutive cycles to flag stagnation


def read_current_score(score_file=None):
    """Read current autonomy score from source file."""
    sf = score_file or SCORE_FILE
    if not sf.exists():
        return None
    data = json.loads(sf.read_text(encoding="utf-8"))
    return {"score": data.get("score"), "ts": data.get("computed_at", "")}


def read_history(history_file=None):
    """Read history of past scores."""
    hf = history_file or HISTORY_FILE
    if not hf.exists():
        return []
    entries = []
    for line in hf.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def write_history_entry(entry, history_file=None):
    """Append a new entry to history."""
    hf = history_file or HISTORY_FILE
    hf.parent.mkdir(parents=True, exist_ok=True)
    with open(hf, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def write_alert(alert_type, message, severity="warning", alerts_file=None):
    """Write an alert to the shared alerts file."""
    af = alerts_file or ALERTS_FILE
    af.parent.mkdir(parents=True, exist_ok=True)
    alert = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "verifier",
        "type": f"autonomy_{alert_type}",
        "severity": severity,
        "message": message,
    }
    with open(af, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert) + "\n")


def detect_drift(history):
    """Detect regression and stagnation from score history.
    
    Returns list of (type, message) tuples.
    """
    alerts = []
    if len(history) < 2:
        return alerts
    
    # Check for regression: drop > DROP_THRESHOLD in single step
    for i in range(1, len(history)):
        prev = history[i-1]["score"]
        curr = history[i]["score"]
        delta = prev - curr  # positive = drop
        if delta > DROP_THRESHOLD:
            alerts.append(("regression", 
                f"Autonomy score dropped {delta:.1f} pts ({prev:.1f} -> {curr:.1f}) "
                f"between {history[i-1]['ts'][:10]} and {history[i]['ts'][:10]}"))
    
    # Check for stagnation: plateau within +/-PLATEAU_TOL per step for PLATEAU_CYCLES+ consecutive
    if len(history) >= PLATEAU_CYCLES + 1:
        recent = history[-(PLATEAU_CYCLES+1):]
        scores = [e["score"] for e in recent]
        # All consecutive pairs within tolerance
        plateau = all(abs(scores[i+1] - scores[i]) <= PLATEAU_TOL 
                     for i in range(len(scores)-1))
        if plateau:
            avg = sum(scores) / len(scores)
            alerts.append(("stagnation",
                f"Autonomy score plateaued at ~{avg:.1f} "
                f"for {len(scores)} consecutive cycles (max_step_delta={max(abs(scores[i+1]-scores[i]) for i in range(len(scores)-1)):.2f})"))
    
    return alerts


def run_live():
    """Run the drift detector on live data."""
    current = read_current_score()
    if current is None:
        print("[autonomy_drift_detector] NO_DATA: autonomy-score.json not found")
        return 0
    
    history = read_history()
    
    # Add current reading to history (deduplicate by ts)
    existing_ts = {e.get("ts", "") for e in history}
    if current["ts"] and current["ts"] not in existing_ts:
        entry = {"score": current["score"], "ts": current["ts"]}
        write_history_entry(entry)
        history.append(entry)
    
    alerts = detect_drift(history)
    
    print(f"[autonomy_drift_detector] score={current['score']:.1f} history_len={len(history)}")
    for alert_type, msg in alerts:
        severity = "critical" if alert_type == "regression" else "warning"
        write_alert(alert_type, msg, severity)
        print(f"  ALERT [{alert_type}] {msg}")
    
    if not alerts:
        print("  No drift detected (no regression, no stagnation)")
    
    # Write report
    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "current_score": current["score"],
        "history_len": len(history),
        "alerts": [{"type": t, "message": m} for t, m in alerts],
        "status": "ALERT" if alerts else "OK",
    }
    report_file = REPO_ROOT / "memory" / "verifier" / "autonomy-drift-report.json"
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"  Report: {report_file.relative_to(REPO_ROOT)}")
    
    return 0


def self_test():
    """Run synthetic tests."""
    import tempfile, shutil
    
    results = []
    test_dir = Path(tempfile.mkdtemp())
    try:
        # T1: empty history -> no alerts
        alerts = detect_drift([])
        results.append(("T1_empty_no_alerts", len(alerts) == 0))
        
        # T2: single entry -> no alerts
        alerts = detect_drift([{"score": 70.0, "ts": "2026-11-20"}])
        results.append(("T2_single_no_alerts", len(alerts) == 0))
        
        # T3: drop > 10 -> regression detected
        h = [
            {"score": 75.0, "ts": "2026-11-20"},
            {"score": 64.0, "ts": "2026-11-21"},  # drop of 11
        ]
        alerts = detect_drift(h)
        regression = any(t == "regression" for t, _ in alerts)
        results.append(("T3_regression_detected", regression))
        
        # T4: small drop (5 pts) -> no regression
        h = [
            {"score": 75.0, "ts": "2026-11-20"},
            {"score": 70.0, "ts": "2026-11-21"},  # drop of 5
        ]
        alerts = detect_drift(h)
        regression = any(t == "regression" for t, _ in alerts)
        results.append(("T4_small_drop_no_regression", not regression))
        
        # T5: plateau for 4 cycles -> stagnation detected
        h = [
            {"score": 70.0, "ts": "2026-11-18"},
            {"score": 70.5, "ts": "2026-11-19"},
            {"score": 69.8, "ts": "2026-11-20"},
            {"score": 70.2, "ts": "2026-11-21"},
        ]
        alerts = detect_drift(h)
        stagnation = any(t == "stagnation" for t, _ in alerts)
        results.append(("T5_stagnation_detected", stagnation))
        
        # T6: varying scores -> no stagnation
        h = [
            {"score": 70.0, "ts": "2026-11-18"},
            {"score": 73.0, "ts": "2026-11-19"},
            {"score": 68.0, "ts": "2026-11-20"},
            {"score": 75.0, "ts": "2026-11-21"},
        ]
        alerts = detect_drift(h)
        stagnation = any(t == "stagnation" for t, _ in alerts)
        results.append(("T6_no_stagnation_varying", not stagnation))
        
        # T7: boundary - exactly 10 point drop -> NOT flagged (strict >)
        h = [
            {"score": 80.0, "ts": "2026-11-20"},
            {"score": 70.0, "ts": "2026-11-21"},  # exactly 10 drop
        ]
        alerts = detect_drift(h)
        regression = any(t == "regression" for t, _ in alerts)
        results.append(("T7_boundary_10_not_flagged", not regression))
        
        # T8: boundary - just over 10 -> flagged
        h = [
            {"score": 80.0, "ts": "2026-11-20"},
            {"score": 69.9, "ts": "2026-11-21"},  # 10.1 drop
        ]
        alerts = detect_drift(h)
        regression = any(t == "regression" for t, _ in alerts)
        results.append(("T8_just_over_10_flagged", regression))
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
    
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"[self-test] {passed} passed / {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    else:
        sys.exit(run_live())
