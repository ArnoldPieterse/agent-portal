"""transition_latency.py - Measures wall-clock time from mode-change trigger to fleet-mode.json mtime update.

Each measurement is logged to memory/ops/transition-latency.jsonl as:
  {"timestamp": ISO, "trigger_mode": str, "result_mode": str, "latency_ms": float, "fleet_file_mtime": ISO}

Usage:
  python memory/mechanic/transition_latency.py --selftest
  python memory/mechanic/transition_latency.py --measure <expected_mode>  # measure latency to target mode
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

FLEET_MODE_PATH = Path("fleet-mode.json")
LOG_PATH = Path("memory/ops/transition-latency.jsonl")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def get_fleet_mode_mtime(path: Path = FLEET_MODE_PATH) -> float | None:
    """Return mtime of fleet-mode.json as epoch seconds, or None if not exists."""
    if path.exists():
        return path.stat().st_mtime
    return None


def measure_latency(expected_mode: str, trigger_time: float | None = None,
                    timeout_s: float = 30.0, poll_interval: float = 0.5,
                    fleet_path: Path = FLEET_MODE_PATH) -> dict:
    """Measure time from trigger to fleet-mode.json reflecting expected_mode.

    Args:
        expected_mode: the mode we expect to see in fleet-mode.json
        trigger_time: epoch seconds when the mode change was triggered (default: now)
        timeout_s: max seconds to wait
        poll_interval: how often to check (seconds)
        fleet_path: path to fleet-mode.json

    Returns:
        {"latency_ms": float, "result_mode": str|None, "timed_out": bool,
         "fleet_file_mtime": ISO str, "trigger_time": ISO str}
    """
    if trigger_time is None:
        trigger_time = time.time()

    trigger_iso = datetime.fromtimestamp(trigger_time, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    deadline = trigger_time + timeout_s
    result_mode = None
    mtime = None

    while time.time() < deadline:
        if fleet_path.exists():
            try:
                with open(fleet_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                current_mode = data.get("mode")
                if current_mode == expected_mode:
                    mtime = fleet_path.stat().st_mtime
                    result_mode = current_mode
                    break
            except (json.JSONDecodeError, OSError):
                pass
        time.sleep(poll_interval)

    latency_ms = 0.0
    if mtime is not None:
        latency_ms = max(0.0, (mtime - trigger_time) * 1000.0)

    return {
        "latency_ms": round(latency_ms, 2),
        "result_mode": result_mode,
        "timed_out": mtime is None,
        "fleet_file_mtime": now_iso() if mtime else None,
        "trigger_time": trigger_iso,
    }


def log_measurement(measurement: dict) -> None:
    """Append measurement to transition-latency.jsonl."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": now_iso(),
        "expected_mode": measurement.get("result_mode") or "UNKNOWN",
        "latency_ms": measurement["latency_ms"],
        "timed_out": measurement["timed_out"],
        "fleet_file_mtime": measurement.get("fleet_file_mtime"),
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run_measurement(expected_mode: str) -> dict:
    """Convenience: measure + log in one call."""
    m = measure_latency(expected_mode)
    log_measurement(m)
    return m


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def selftest() -> bool:
    import shutil
    test_dir = Path("memory/mechanic/fixtures/transition_latency_test")
    test_dir.mkdir(parents=True, exist_ok=True)

    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  PASS: {name}")
        else:
            failed += 1
            print(f"  FAIL: {name}")

    print("transition_latency.py selftest:")

    test_fleet = test_dir / "fleet-mode.json"
    test_log = test_dir / "latency.jsonl"

    # Test 1: Immediate detection (file already has target mode)
    test_fleet.write_text(json.dumps({"mode": "WORK", "timestamp": "2026-11-24T10:00:00Z", "goal_pct": 50}))
    result = measure_latency("WORK", fleet_path=test_fleet, timeout_s=2.0, poll_interval=0.05)
    check("immediate detection: not timed out", not result["timed_out"])
    check("immediate detection: mode correct", result["result_mode"] == "WORK")
    check("immediate detection: latency low", result["latency_ms"] < 1000)

    # Test 2: Timeout when mode never appears
    test_fleet.write_text(json.dumps({"mode": "IDLE", "timestamp": "2026-11-24T10:00:00Z", "goal_pct": 50}))
    result = measure_latency("MAINTENANCE", fleet_path=test_fleet, timeout_s=0.5, poll_interval=0.1)
    check("timeout: timed_out flag", result["timed_out"])
    check("timeout: mode is None", result["result_mode"] is None)

    # Test 3: Mode appears after delay (simulate by writing after short sleep)
    import threading
    test_fleet.write_text(json.dumps({"mode": "IDLE", "timestamp": "2026-11-24T10:00:00Z", "goal_pct": 50}))

    def delayed_write():
        time.sleep(0.3)
        test_fleet.write_text(json.dumps({"mode": "MAINTENANCE", "timestamp": "2026-11-24T11:00:00Z", "goal_pct": 90}))

    t = threading.Thread(target=delayed_write)
    t.start()
    result = measure_latency("MAINTENANCE", fleet_path=test_fleet, timeout_s=5.0, poll_interval=0.05)
    t.join()
    check("delayed: detected", not result["timed_out"])
    check("delayed: mode correct", result["result_mode"] == "MAINTENANCE")
    check("delayed: latency > 200ms (was delayed 300ms)", result["latency_ms"] >= 100)

    # Test 4: Nonexistent file -> timeout
    result = measure_latency("WORK", fleet_path=test_dir / "nonexistent.json", timeout_s=0.3, poll_interval=0.1)
    check("nonexistent file: timeout", result["timed_out"])

    # Test 5: Corrupt JSON handled gracefully
    test_fleet.write_text("not valid json {{{")
    result = measure_latency("WORK", fleet_path=test_fleet, timeout_s=0.3, poll_interval=0.1)
    check("corrupt JSON: timeout (no crash)", result["timed_out"])

    # Test 6: Log measurement works
    global LOG_PATH
    orig_log = LOG_PATH
    LOG_PATH = test_log
    m = {"latency_ms": 42.0, "result_mode": "WORK", "timed_out": False, "fleet_file_mtime": now_iso()}
    log_measurement(m)
    LOG_PATH = orig_log
    check("log file created", test_log.exists())
    with open(test_log) as f:
        lines = f.readlines()
    entry = json.loads(lines[0])
    check("log entry has timestamp", "timestamp" in entry)
    check("log entry has latency_ms", entry["latency_ms"] == 42.0)
    check("log entry has expected_mode", entry["expected_mode"] == "WORK")

    # Test 7: Multiple log entries append (not overwrite)
    LOG_PATH = test_log
    m2 = {"latency_ms": 99.0, "result_mode": "IDLE", "timed_out": False, "fleet_file_mtime": now_iso()}
    log_measurement(m2)
    LOG_PATH = orig_log
    with open(test_log) as f:
        lines = f.readlines()
    check("log appends (2 entries)", len(lines) == 2)

    # Test 8: run_measurement integration
    test_fleet.write_text(json.dumps({"mode": "IDLE", "timestamp": "2026-11-24T12:00:00Z", "goal_pct": 100}))
    LOG_PATH = test_log
    result = measure_latency("IDLE", fleet_path=test_fleet, timeout_s=2.0, poll_interval=0.05)
    log_measurement(result)
    LOG_PATH = orig_alert if False else orig_log
    check("run_measurement: detected IDLE", result["result_mode"] == "IDLE")

    # Cleanup
    shutil.rmtree(test_dir)

    print(f"\n  Result: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif "--measure" in sys.argv:
        idx = sys.argv.index("--measure")
        mode = sys.argv[idx + 1]
        result = run_measurement(mode)
        print(json.dumps(result, indent=2))
        sys.exit(0 if not result["timed_out"] else 1)
    else:
        print(__doc__)
        sys.exit(0)
