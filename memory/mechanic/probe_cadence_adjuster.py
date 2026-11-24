#!/usr/bin/env python3
"""probe_cadence_adjuster.py - Auto-adjust probe cadence based on fleet mode.

STEADY-STATE: reduce from 5min to 15min. On exit, restore. Log all changes.
Verification: mode change triggers within 1 probe cycle; no missed detections (simulated).

Usage: python memory/mechanic/probe_cadence_adjuster.py [--selftest]
"""
import json, os, sys
from datetime import datetime, timezone

MODE_PATH = os.path.join("memory", "ops", "fleet-mode.json")
MATRIX_PATH = os.path.join("memory", "ops", "seat-matrix.json")
CADENCE_LOG = os.path.join("memory", "ops", "probe-cadence-log.jsonl")

WORK_INTERVAL = 5      # minutes
STEADY_INTERVAL = 15   # minutes


def read_mode():
    """Read current fleet mode from fleet-mode.json."""
    if not os.path.exists(MODE_PATH):
        return None
    try:
        with open(MODE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("mode")
    except (json.JSONDecodeError, OSError):
        return None


def read_current_interval():
    """Read current probe interval from seat-matrix.json."""
    if not os.path.exists(MATRIX_PATH):
        return WORK_INTERVAL
    try:
        with open(MATRIX_PATH, "r", encoding="utf-8") as f:
            m = json.load(f)
        return m.get("probe_interval_min", WORK_INTERVAL)
    except (json.JSONDecodeError, OSError):
        return WORK_INTERVAL


def set_interval(new_interval):
    """Write new probe interval to seat-matrix.json."""
    if not os.path.exists(MATRIX_PATH):
        # Create minimal matrix if missing
        m = {"probe_interval_min": new_interval, "seats": {}}
    else:
        with open(MATRIX_PATH, "r", encoding="utf-8") as f:
            m = json.load(f)
    m["probe_interval_min"] = new_interval
    os.makedirs(os.path.dirname(MATRIX_PATH), exist_ok=True)
    with open(MATRIX_PATH, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)


def log_change(from_min, to_min, reason):
    """Append cadence change to probe-cadence-log.jsonl."""
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "from_min": from_min,
        "to_min": to_min,
        "reason": reason,
    }
    os.makedirs(os.path.dirname(CADENCE_LOG), exist_ok=True)
    with open(CADENCE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def adjust():
    """Main adjustment logic: compare desired vs current interval."""
    mode = read_mode()
    current = read_current_interval()
    
    if mode == "STEADY-STATE":
        desired = STEADY_INTERVAL
    else:
        desired = WORK_INTERVAL  # WORK or any other mode -> full cadence
    
    if current != desired:
        log_change(current, desired, f"mode={mode}")
        set_interval(desired)
        return {"changed": True, "from": current, "to": desired, "mode": mode}
    return {"changed": False, "current": current, "mode": mode}


def selftest():
    """Simulate mode change: STEADY-STATE triggers 15min; WORK restores 5min."""
    import tempfile, shutil
    ok = True
    def check(name, cond):
        nonlocal ok
        print(("PASS" if cond else "FAIL"), name)
        ok = ok and bool(cond)

    # Use temp files to avoid clobbering real state
    tmpdir = tempfile.mkdtemp()
    global MODE_PATH, MATRIX_PATH, CADENCE_LOG
    orig_mode, orig_matrix, orig_log = MODE_PATH, MATRIX_PATH, CADENCE_LOG
    MODE_PATH = os.path.join(tmpdir, "fleet-mode.json")
    MATRIX_PATH = os.path.join(tmpdir, "seat-matrix.json")
    CADENCE_LOG = os.path.join(tmpdir, "probe-cadence-log.jsonl")

    try:
        # Initial state: WORK mode, 5min interval
        with open(MODE_PATH, "w") as f:
            json.dump({"mode": "WORK"}, f)
        with open(MATRIX_PATH, "w") as f:
            json.dump({"probe_interval_min": 5, "seats": {}}, f)

        # No change expected in WORK mode
        r = adjust()
        check("WORK: no change", r["changed"] is False and r["current"] == 5)

        # Switch to STEADY-STATE -> should trigger 15min within 1 cycle
        with open(MODE_PATH, "w") as f:
            json.dump({"mode": "STEADY-STATE"}, f)
        r = adjust()
        check("STEADY-STATE: changed to 15", r["changed"] is True and r["to"] == 15)

        # Verify interval was written
        with open(MATRIX_PATH) as f:
            m = json.load(f)
        check("STEADY-STATE: matrix updated", m["probe_interval_min"] == 15)

        # Switch back to WORK -> should restore 5min
        with open(MODE_PATH, "w") as f:
            json.dump({"mode": "WORK"}, f)
        r = adjust()
        check("WORK restore: changed to 5", r["changed"] is True and r["to"] == 5)

        # Verify log has 2 entries (one for each change)
        with open(CADENCE_LOG) as f:
            logs = [json.loads(l) for l in f if l.strip()]
        check("log: 2 entries", len(logs) == 2)
        check("log: first is 5->15", logs[0]["from_min"] == 5 and logs[0]["to_min"] == 15)
        check("log: second is 15->5", logs[1]["from_min"] == 15 and logs[1]["to_min"] == 5)

        # No missed detection: if mode changes again, it triggers immediately
        with open(MODE_PATH, "w") as f:
            json.dump({"mode": "STEADY-STATE"}, f)
        r = adjust()
        check("re-enter STEADY: immediate trigger", r["changed"] is True and r["to"] == 15)

    finally:
        MODE_PATH, MATRIX_PATH, CADENCE_LOG = orig_mode, orig_matrix, orig_log
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    result = adjust()
    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
