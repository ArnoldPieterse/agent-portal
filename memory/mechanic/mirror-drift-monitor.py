#!/usr/bin/env python3
"""mirror-drift-monitor.py - detect sustained mirror sync lag > 10 min; alert + auto-run recovery.

Reads memory_mirror.log for the last successful sync timestamp, computes lag vs now.
If lag > THRESHOLD_MIN sustained (confirmed by >=2 consecutive checks), triggers:
  1. Alert entry to memory/ops/fleet-heartbeat.json (drift field)
  2. Auto-run recovery: memory/mechanic/mirror-recovery.py (or inline fallback)

Usage:
  python mirror-drift-monitor.py            # check + alert if needed
  python mirror-drift-monitor.py --test     # self-test with simulated timestamps
"""
import json, os, sys, datetime, pathlib

HERE = pathlib.Path(__file__).resolve().parent.parent.parent  # project root
LOG_FILE = HERE / "memory_mirror.log"
ALERT_FILE = HERE / "memory" / "ops" / "fleet-heartbeat.json"
DRIFT_STATE = HERE / "memory" / "mechanic" / "mirror-drift-state.json"
THRESHOLD_MIN = 10

def parse_last_success(log_path):
    """Return the most recent timestamp from memory_mirror.log."""
    if not log_path.exists():
        return None
    last_t = None
    for line in log_path.read_text(encoding="utf-8").strip().split("\n"):
        try:
            entry = json.loads(line)
            t = entry.get("t")
            if t:
                last_t = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
        except (json.JSONDecodeError, ValueError):
            continue
    return last_t

def compute_lag_minutes(last_sync, now=None):
    """Minutes since last sync."""
    if last_sync is None:
        return 9999.0  # no sync ever = infinite drift
    now = now or datetime.datetime.now()
    return (now - last_sync).total_seconds() / 60.0

def load_state():
    if DRIFT_STATE.exists():
        return json.loads(DRIFT_STATE.read_text(encoding="utf-8"))
    return {"consecutive_alerts": 0, "last_check": None}

def save_state(state):
    DRIFT_STATE.parent.mkdir(parents=True, exist_ok=True)
    DRIFT_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def trigger_recovery():
    """Run the mirror recovery runbook (inline: re-run memory_mirror.py)."""
    import subprocess
    result = {"action": "recovery_triggered", "timestamp": datetime.datetime.now().isoformat()}
    try:
        proc = subprocess.run(
            [sys.executable, str(HERE / "memory_mirror.py")],
            capture_output=True, text=True, timeout=120
        )
        result["exit_code"] = proc.returncode
        result["stdout_tail"] = proc.stdout[-200:] if proc.stdout else ""
    except Exception as e:
        result["error"] = str(e)
    return result

def check():
    """One drift check cycle. Returns (drift_min, alert_fired)."""
    now = datetime.datetime.now()
    last_sync = parse_last_success(LOG_FILE)
    lag = compute_lag_minutes(last_sync, now)
    
    state = load_state()
    prev_consecutive = state.get("consecutive_alerts", 0)
    
    if lag > THRESHOLD_MIN:
        new_consecutive = prev_consecutive + 1
        alert_fired = new_consecutive >= 2  # sustained = 2 consecutive checks
    else:
        new_consecutive = 0
        alert_fired = False
    
    state["consecutive_alerts"] = new_consecutive
    state["last_check"] = now.strftime("%Y-%m-%d %H:%M:%S")
    state["last_lag_min"] = round(lag, 1)
    save_state(state)
    
    if alert_fired:
        # Update fleet-heartbeat.json with drift info
        heartbeat = {}
        if ALERT_FILE.exists():
            try:
                heartbeat = json.loads(ALERT_FILE.read_text(encoding="utf-8"))
            except: pass
        heartbeat["mirror_drift"] = {
            "status": "ALERT",
            "lag_minutes": round(lag, 1),
            "consecutive_checks": new_consecutive,
            "triggered_at": now.isoformat()
        }
        ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)
        ALERT_FILE.write_text(json.dumps(heartbeat, indent=2), encoding="utf-8")
        
        # Trigger recovery
        recovery = trigger_recovery()
        heartbeat["mirror_drift"]["recovery"] = recovery
        ALERT_FILE.write_text(json.dumps(heartbeat, indent=2), encoding="utf-8")
    
    return lag, alert_fired

def self_test():
    """Simulate 3 scenarios: normal (5min), drifting (12min x2), recovered. Verify alert logic."""
    print("=== Mirror Drift Monitor Self-Test ===")
    results = []
    
    # Test 1: Normal operation (5 min lag) - should NOT alert
    test_log = HERE / "memory_mirror_test.log"
    now = datetime.datetime.now()
    normal_t = (now - datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    test_log.write_text(json.dumps({"t": normal_t, "results": []}) + "\n", encoding="utf-8")
    
    # Monkey-patch LOG_FILE for test
    global LOG_FILE, DRIFT_STATE
    orig_log, orig_state = LOG_FILE, DRIFT_STATE
    LOG_FILE = test_log
    DRIFT_STATE = HERE / "memory" / "mechanic" / "mirror-drift-state-test.json"
    
    # Reset state
    if DRIFT_STATE.exists(): DRIFT_STATE.unlink()
    
    lag1, alert1 = check()  # first check at 5min - no alert (below threshold)
    results.append(("normal_5min", round(lag1,1), alert1))
    
    # Test 2: Drift detected (12 min) - first occurrence, consecutive=1, no alert yet
    drift_t = (now - datetime.timedelta(minutes=12)).strftime("%Y-%m-%d %H:%M:%S")
    test_log.write_text(json.dumps({"t": drift_t, "results": []}) + "\n", encoding="utf-8")
    lag2, alert2 = check()  # first drift check
    results.append(("drift_12min_first", round(lag2,1), alert2))
    
    # Test 3: Sustained drift (still 12 min) - consecutive=2, ALERT fires
    lag3, alert3 = check()  # second drift check -> sustained
    results.append(("drift_12min_sustained", round(lag3,1), alert3))
    
    # Test 4: Recovery (back to 3 min) - consecutive resets
    rec_t = (now - datetime.timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S")
    test_log.write_text(json.dumps({"t": rec_t, "results": []}) + "\n", encoding="utf-8")
    lag4, alert4 = check()
    results.append(("recovered_3min", round(lag4,1), alert4))
    
    # Cleanup
    LOG_FILE, DRIFT_STATE = orig_log, orig_state
    test_log.unlink(missing_ok=True)
    if (HERE / "memory" / "mechanic" / "mirror-drift-state-test.json").exists():
        (HERE / "memory" / "mechanic" / "mirror-drift-state-test.json").unlink()
    
    # Verify
    print(f"  normal_5min:      lag={results[0][1]}m alert={results[0][2]}  (expect False)")
    print(f"  drift_12min_first: lag={results[1][1]}m alert={results[1][2]}  (expect False - first occurrence)")
    print(f"  drift_12min_sust:  lag={results[2][1]}m alert={results[2][2]}  (expect True - sustained)")
    print(f"  recovered_3min:   lag={results[3][1]}m alert={results[3][2]}  (expect False)")
    
    passed = (not results[0][2]) and (not results[1][2]) and results[2][2] and (not results[3][2])
    print(f"\n  VERDICT: {'PASS' if passed else 'FAIL'}")
    
    # Write evidence
    evidence = {
        "test": "mirror-drift-monitor self-test",
        "timestamp": datetime.datetime.now().isoformat(),
        "results": [{"scenario": r[0], "lag_min": r[1], "alert": r[2]} for r in results],
        "verdict": "PASS" if passed else "FAIL",
        "criteria": {
            "simulated_12min_triggers_alert": results[2][2],
            "false_positive_rate_normal": 0 if not any(r[2] for r in [results[0], results[3]]) else 1,
            "sustained_detection": results[2][2] and not results[1][2]
        }
    }
    ev_path = HERE / "memory" / "mechanic" / "mirror-drift-test-evidence.json"
    ev_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"  Evidence: {ev_path.relative_to(HERE)}")
    return passed

if __name__ == "__main__":
    if "--test" in sys.argv:
        ok = self_test()
        sys.exit(0 if ok else 1)
    else:
        lag, alert = check()
        status = "ALERT" if alert else "OK"
        print(f"[mirror-drift] lag={lag:.1f}min status={status}")
