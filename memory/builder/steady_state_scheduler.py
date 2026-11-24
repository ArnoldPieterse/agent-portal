#!/usr/bin/env python3
"""steady_state_scheduler.py - Adapt cycle cadence based on fleet mode.

Goal #3 (Cycle 17): When fleet-mode.json shows mode=STEADY-STATE, change
cycle_daily cadence from daily (86400s) to biweekly (1209600s). On exit
from STEADY-STATE, restore to daily. Logs all changes to
memory/ops/cadence-changes.jsonl.

Usage:
  python memory/builder/steady_state_scheduler.py           # run adaptation check
  python memory/builder/steady_state_scheduler.py --selftest  # verify both transitions
"""
import json, os, sys, time
from datetime import datetime, timezone

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODE_FILE = os.path.join(WS, "memory", "ops", "fleet-mode.json")
SCHED_FILE = os.path.join(WS, "memory", "ops", "scheduler-state.json")
LOG_FILE = os.path.join(WS, "memory", "ops", "cadence-changes.jsonl")

DAILY_INTERVAL = 86400       # 1 day
BIWEEKLY_INTERVAL = 1209600  # 14 days
STATE_KEY = "cycle_daily"    # the scheduler slot we adapt


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_mode():
    """Return current fleet mode string (default WORK if file missing)."""
    try:
        with open(MODE_FILE, encoding="utf-8") as f:
            return json.load(f).get("mode", "WORK")
    except (FileNotFoundError, json.JSONDecodeError):
        return "WORK"


def read_scheduler():
    """Return scheduler-state dict."""
    with open(SCHED_FILE, encoding="utf-8") as f:
        return json.load(f)


def write_scheduler(state):
    with open(SCHED_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1)


def log_change(from_interval, to_interval, reason, mode):
    """Append a cadence change record."""
    entry = {
        "ts": _now_iso(),
        "from_interval": from_interval,
        "to_interval": to_interval,
        "reason": reason,
        "mode": mode,
        "source": "steady_state_scheduler.py",
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def adapt():
    """Main adaptation logic. Returns (changed: bool, message: str)."""
    mode = read_mode()
    sched = read_scheduler()
    slot = sched.get(STATE_KEY)
    if slot is None:
        return False, f"ERROR: {STATE_KEY} not found in scheduler-state.json"

    current_interval = slot["interval"]

    if mode == "STEADY-STATE":
        if current_interval == DAILY_INTERVAL:
            # Transition to biweekly
            old = current_interval
            slot["interval"] = BIWEEKLY_INTERVAL
            slot["note"] = (slot.get("note", "") + " | steady-state 2026-11: cadence daily->biweekly").strip()
            # Recompute next_run from now + biweekly
            slot["next_run"] = time.time() + BIWEEKLY_INTERVAL
            write_scheduler(sched)
            log_change(old, BIWEEKLY_INTERVAL, "steady-state entry", mode)
            return True, f"STEADY-STATE: cadence {old}s -> {BIWEEKLY_INTERVAL}s (biweekly)"
        elif current_interval == BIWEEKLY_INTERVAL:
            return False, "Already in biweekly cadence (steady-state active)"
        else:
            return False, f"Unexpected interval {current_interval}; not touching"
    else:
        if current_interval == BIWEEKLY_INTERVAL:
            # Rollback to daily
            old = current_interval
            slot["interval"] = DAILY_INTERVAL
            slot["note"] = (slot.get("note", "") + " | steady-state exit: cadence restored to daily").strip()
            slot["next_run"] = time.time() + DAILY_INTERVAL
            write_scheduler(sched)
            log_change(old, DAILY_INTERVAL, "steady-state exit (rollback)", mode)
            return True, f"ROLLBACK: cadence {old}s -> {DAILY_INTERVAL}s (daily restored, mode={mode})"
        elif current_interval == DAILY_INTERVAL:
            return False, f"Normal daily cadence (mode={mode})"
        else:
            return False, f"Unexpected interval {current_interval} in non-steady mode; not touching"


def selftest():
    """Simulate both transitions without touching real files.
    Uses temp copies to verify logic."""
    import tempfile, shutil

    print("=== steady_state_scheduler.py --selftest ===")
    passed = 0
    failed = 0

    # Create a sandbox with mock files
    tmpdir = tempfile.mkdtemp(prefix="ss_sched_test_")
    try:
        mode_path = os.path.join(tmpdir, "fleet-mode.json")
        sched_path = os.path.join(tmpdir, "scheduler-state.json")
        log_path = os.path.join(tmpdir, "cadence-changes.jsonl")

        # Patch module-level paths for test
        global MODE_FILE, SCHED_FILE, LOG_FILE
        orig_mode, orig_sched, orig_log = MODE_FILE, SCHED_FILE, LOG_FILE
        MODE_FILE, SCHED_FILE, LOG_FILE = mode_path, sched_path, log_path

        def write_mode(m):
            with open(mode_path, "w") as f:
                json.dump({"mode": m}, f)

        def write_sched(interval=DAILY_INTERVAL):
            state = {
                STATE_KEY: {
                    "name": STATE_KEY,
                    "interval": interval,
                    "note": "test",
                    "daily": [3, 0],
                    "next_run": time.time() + interval,
                    "last_run": time.time() - interval,
                    "last_rc": 0,
                    "last_err": "",
                    "runs": 10,
                    "paused": False,
                    "running": False,
                }
            }
            with open(sched_path, "w") as f:
                json.dump(state, f)

        # Test 1: STEADY-STATE entry (daily -> biweekly)
        write_mode("STEADY-STATE")
        write_sched(DAILY_INTERVAL)
        changed, msg = adapt()
        assert changed is True, f"T1: expected change, got {msg}"
        sched_after = read_scheduler()
        assert sched_after[STATE_KEY]["interval"] == BIWEEKLY_INTERVAL, \
            f"T1: interval not biweekly: {sched_after[STATE_KEY]['interval']}"
        print(f"  PASS T1: steady-state entry -> {msg}")
        passed += 1

        # Test 2: Already steady (no-op)
        changed, msg = adapt()
        assert changed is False, f"T2: expected no change, got {msg}"
        print(f"  PASS T2: idempotent steady-state -> {msg}")
        passed += 1

        # Test 3: Rollback (biweekly -> daily on mode exit)
        write_mode("WORK")
        changed, msg = adapt()
        assert changed is True, f"T3: expected rollback, got {msg}"
        sched_after = read_scheduler()
        assert sched_after[STATE_KEY]["interval"] == DAILY_INTERVAL, \
            f"T3: interval not daily: {sched_after[STATE_KEY]['interval']}"
        print(f"  PASS T3: rollback on exit -> {msg}")
        passed += 1

        # Test 4: Already daily (no-op)
        changed, msg = adapt()
        assert changed is False, f"T4: expected no change, got {msg}"
        print(f"  PASS T4: idempotent daily -> {msg}")
        passed += 1

        # Test 5: Log file has exactly 2 entries (T1 + T3)
        with open(log_path, encoding="utf-8") as f:
            lines = [l for l in f.read().strip().splitlines() if l.strip()]
        assert len(lines) == 2, f"T5: expected 2 log entries, got {len(lines)}"
        e1 = json.loads(lines[0])
        e2 = json.loads(lines[1])
        assert e1["from_interval"] == DAILY_INTERVAL and e1["to_interval"] == BIWEEKLY_INTERVAL
        assert e2["from_interval"] == BIWEEKLY_INTERVAL and e2["to_interval"] == DAILY_INTERVAL
        assert "source" in e1 and "mode" in e1
        print(f"  PASS T5: log entries correct ({len(lines)} entries)")
        passed += 1

        # Test 6: STEADY-STATE with unexpected interval (no touch)
        write_mode("STEADY-STATE")
        write_sched(3600)  # hourly - unexpected
        changed, msg = adapt()
        assert changed is False, f"T6: expected no change for unexpected interval"
        sched_after = read_scheduler()
        assert sched_after[STATE_KEY]["interval"] == 3600
        print(f"  PASS T6: unexpected interval untouched -> {msg}")
        passed += 1

    finally:
        # Restore originals
        MODE_FILE, SCHED_FILE, LOG_FILE = orig_mode, orig_sched, orig_log
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"\nResult: {passed}/6 tests passed")
    if failed == 0 and passed == 6:
        print("SELFTEST PASS")
        return 0
    else:
        print("SELFTEST FAIL")
        return 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    else:
        changed, msg = adapt()
        status = "CHANGED" if changed else "NO-OP"
        print(f"[{status}] {msg}")
        sys.exit(0)
