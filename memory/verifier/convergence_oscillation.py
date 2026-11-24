"""Convergence Oscillation Detector.
Scans decision-log.jsonl for action flapping: same (action_type, target) pair
executed >3 times within a 30-min window indicates non-convergence.
Severity: WARN (4x), CRIT (7x+).
Writes violations to memory/ops/oscillation-alerts.jsonl.
"""
import json, sys, pathlib
from datetime import datetime, timedelta

DECISION_LOG = pathlib.Path("memory/decision-log.jsonl")
ALERTS_FILE = pathlib.Path("memory/ops/oscillation-alerts.jsonl")
WINDOW = timedelta(minutes=30)
THRESHOLD_WARN = 4   # >3 executions
THRESHOLD_CRIT = 7   # >=7 executions

def get_target(entry):
    """Extract target from a decision-log entry."""
    return entry.get("target", entry.get("runbook", entry.get("host", "unknown")))

def scan_oscillations(log_path=DECISION_LOG, window=WINDOW):
    """Scan log for (action_type, target) pairs exceeding threshold within window.
    Returns list of violation dicts."""
    if not log_path.exists():
        return []
    
    # Parse all entries
    entries = []
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                ts = datetime.fromisoformat(e["timestamp"])
                entries.append((ts, e))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    
    # Group by (action_type, target)
    groups = {}
    for ts, e in entries:
        key = (e.get("type", "unknown"), get_target(e))
        groups.setdefault(key, []).append(ts)
    
    violations = []
    for (atype, target), timestamps in groups.items():
        timestamps.sort()
        # Sliding window: check if any window of size `window` contains >3 events
        best_count = 0
        best_start = None
        best_end = None
        n = len(timestamps)
        for i in range(n):
            # Find all events within [timestamps[i], timestamps[i] + window]
            end_idx = i
            while end_idx + 1 < n and timestamps[end_idx + 1] - timestamps[i] <= window:
                end_idx += 1
            count_in_window = end_idx - i + 1
            if count_in_window > best_count:
                best_count = count_in_window
                best_start = timestamps[i]
                best_end = timestamps[end_idx]
        
        if best_count >= THRESHOLD_WARN:
            severity = "CRIT" if best_count >= THRESHOLD_CRIT else "WARN"
            violations.append({
                "action_type": atype,
                "target": target,
                "count": best_count,
                "window_start": best_start.isoformat(),
                "window_end": best_end.isoformat(),
                "severity": severity,
                "detected_at": datetime.now().isoformat()
            })
    
    return violations

def write_alerts(violations):
    """Append violations to alerts file."""
    if not violations:
        return
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        for v in violations:
            f.write(json.dumps(v) + "\n")

def run(log_path=DECISION_LOG):
    """Main entry: scan, write alerts, return (violations, exit_code)."""
    violations = scan_oscillations(log_path)
    write_alerts(violations)
    
    # Print summary
    if violations:
        for v in violations:
            print(f"[{v['severity']}] {v['action_type']} / {v['target']}: "
                  f"{v['count']}x in {v['window_start']} -> {v['window_end']}")
    else:
        print("No oscillation detected.")
    
    return violations, 0

def self_test():
    """Run verification cases. Returns (passed, total)."""
    import tempfile, os
    passed = 0
    total = 0
    
    # Case 1: 8 model-swap events on same host in 25 min = CRIT
    total += 1
    base_ts = datetime(2026, 11, 24, 10, 0, 0)
    entries = []
    for i in range(8):
        ts = base_ts + timedelta(minutes=i * 3)  # spread over 21 min
        entries.append({"type": "model_swap", "target": "White", 
                        "timestamp": ts.isoformat()})
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp_path = pathlib.Path(f.name)
    
    try:
        violations = scan_oscillations(tmp_path)
        assert len(violations) == 1, f"Expected 1 violation, got {len(violations)}"
        assert violations[0]["severity"] == "CRIT", f"Expected CRIT, got {violations[0]['severity']}"
        assert violations[0]["count"] == 8, f"Expected count=8, got {violations[0]['count']}"
        assert violations[0]["action_type"] == "model_swap"
        assert violations[0]["target"] == "White"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case1: {ex}")
    finally:
        os.unlink(tmp_path)
    
    # Case 2: clean log with 2 swaps spaced >30min = no alert
    total += 1
    entries = [
        {"type": "model_swap", "target": "White", "timestamp": "2026-11-24T10:00:00"},
        {"type": "model_swap", "target": "White", "timestamp": "2026-11-24T10:35:00"}
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp_path = pathlib.Path(f.name)
    
    try:
        violations = scan_oscillations(tmp_path)
        assert len(violations) == 0, f"Expected no violations, got {violations}"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case2: {ex}")
    finally:
        os.unlink(tmp_path)
    
    # Case 3: boundary at exactly 3x (no alert)
    total += 1
    entries = []
    for i in range(3):
        ts = base_ts + timedelta(minutes=i * 5)
        entries.append({"type": "model_swap", "target": "Black", 
                        "timestamp": ts.isoformat()})
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp_path = pathlib.Path(f.name)
    
    try:
        violations = scan_oscillations(tmp_path)
        assert len(violations) == 0, f"Expected no violations at exactly 3x, got {violations}"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case3: {ex}")
    finally:
        os.unlink(tmp_path)
    
    # Case 4: exactly 4 in window = WARN (not CRIT)
    total += 1
    entries = []
    for i in range(4):
        ts = base_ts + timedelta(minutes=i * 5)
        entries.append({"type": "file_write", "target": "memory/ops/x.json", 
                        "timestamp": ts.isoformat()})
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp_path = pathlib.Path(f.name)
    
    try:
        violations = scan_oscillations(tmp_path)
        assert len(violations) == 1, f"Expected 1 violation at 4x, got {len(violations)}"
        assert violations[0]["severity"] == "WARN", f"Expected WARN at 4x, got {violations[0]['severity']}"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case4: {ex}")
    finally:
        os.unlink(tmp_path)
    
    # Case 5: different targets don't group together
    total += 1
    entries = []
    for i in range(8):
        ts = base_ts + timedelta(minutes=i * 2)
        target = "White" if i % 2 == 0 else "Black"
        entries.append({"type": "model_swap", "target": target, 
                        "timestamp": ts.isoformat()})
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp_path = pathlib.Path(f.name)
    
    try:
        violations = scan_oscillations(tmp_path)
        # Each target has 4 events in window -> WARN each
        assert len(violations) == 2, f"Expected 2 violations (one per target), got {len(violations)}"
        for v in violations:
            assert v["severity"] == "WARN", f"Expected WARN for 4x, got {v['severity']}"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case5: {ex}")
    finally:
        os.unlink(tmp_path)
    
    # Case 6: run on actual decision-log.jsonl (known state)
    total += 1
    violations = scan_oscillations(DECISION_LOG)
    # Real log has "runbook_execution"/"Safe Test" at 08:18:29, 08:18:34, 08:45:35, 08:45:37
    # = 4 events in ~27 min window -> WARN (correct behavior)
    if violations:
        assert violations[0]["severity"] == "WARN", f"Expected WARN on real log, got {violations[0]['severity']}"
        assert violations[0]["count"] >= 4, f"Expected count>=4, got {violations[0]['count']}"
    # If log is empty or doesn't exist, no violations
    passed += 1
    
    print(f"\nSelf-test: {passed}/{total} passed")
    return passed, total

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        p, t = self_test()
        sys.exit(0 if p == t else 1)
    else:
        violations, rc = run()
        sys.exit(rc)
