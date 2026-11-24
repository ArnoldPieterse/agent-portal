"""fleet_mode_infra.py - Low-level atomic write primitive for fleet-mode.json.

Provides:
  - atomic_write_fleet_mode(path, data): write-to-temp + os.rename with schema validation
  - validate_fleet_mode(data): schema check (mode enum, timestamp ISO-8601, goal_pct range)
  - read_fleet_mode(path): safe reader with error handling

Usage:
  python memory/mechanic/fleet_mode_infra.py --selftest
  python memory/mechanic/fleet_mode_infra.py --write '{"mode":"WORK","timestamp":"2026-11-24T10:00:00Z","goal_pct":55.0}'
"""

import json
import os
import sys
import tempfile
import re
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import msvcrt  # Windows file locking
    _HAS_MSVCRT = True
except ImportError:
    _HAS_MSVCRT = False

VALID_MODES = {"WORK", "MAINTENANCE", "IDLE"}
ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


class FleetModeSchemaError(Exception):
    """Raised when fleet-mode.json data fails schema validation."""
    pass


def validate_fleet_mode(data: dict) -> None:
    """Validate fleet-mode.json schema. Raises FleetModeSchemaError on failure.

    Required fields:
      - mode: one of {WORK, MAINTENANCE, IDLE}
      - timestamp: valid ISO-8601 string (e.g. 2026-11-24T10:00:00Z)
      - goal_pct: float in [0, 100]

    Optional fields:
      - agent_count: int >= 0
      - cycle: str
      - note: str
    """
    if not isinstance(data, dict):
        raise FleetModeSchemaError(f"data must be a dict, got {type(data).__name__}")

    # mode
    mode = data.get("mode")
    if mode is None:
        raise FleetModeSchemaError("missing required field: mode")
    if mode not in VALID_MODES:
        raise FleetModeSchemaError(f"mode must be one of {VALID_MODES}, got {mode!r}")

    # timestamp
    ts = data.get("timestamp")
    if ts is None:
        raise FleetModeSchemaError("missing required field: timestamp")
    if not isinstance(ts, str):
        raise FleetModeSchemaError(f"timestamp must be a string, got {type(ts).__name__}")
    if not ISO8601_RE.match(ts):
        raise FleetModeSchemaError(f"timestamp is not valid ISO-8601: {ts!r}")
    # Double-check it actually parses
    try:
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError as e:
        raise FleetModeSchemaError(f"timestamp failed to parse: {e}")

    # goal_pct
    pct = data.get("goal_pct")
    if pct is None:
        raise FleetModeSchemaError("missing required field: goal_pct")
    if not isinstance(pct, (int, float)):
        raise FleetModeSchemaError(f"goal_pct must be a number, got {type(pct).__name__}")
    if not (0 <= float(pct) <= 100):
        raise FleetModeSchemaError(f"goal_pct must be in [0, 100], got {pct}")

    # Optional: agent_count
    if "agent_count" in data:
        ac = data["agent_count"]
        if not isinstance(ac, int) or ac < 0:
            raise FleetModeSchemaError(f"agent_count must be int >= 0, got {ac!r}")

    # Optional: cycle
    if "cycle" in data and not isinstance(data["cycle"], str):
        raise FleetModeSchemaError(f"cycle must be a string, got {type(data['cycle']).__name__}")

    # Optional: note
    if "note" in data and not isinstance(data["note"], str):
        raise FleetModeSchemaError(f"note must be a string, got {type(data['note']).__name__}")


def _acquire_lock(lock_path: str, timeout: float = 5.0):
    """Acquire an exclusive lock on lock_path using msvcrt (Windows).
    
    Returns the file object holding the lock (caller must close it to release).
    Raises TimeoutError if lock cannot be acquired within timeout seconds.
    """
    if not _HAS_MSVCRT:
        # Fallback: no locking on non-Windows (POSIX rename is atomic anyway)
        return None
    
    lock_file = open(lock_path, 'w')
    deadline = time.monotonic() + timeout
    while True:
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return lock_file
        except OSError:
            if time.monotonic() >= deadline:
                lock_file.close()
                raise TimeoutError(f"Could not acquire lock on {lock_path} within {timeout}s")
            time.sleep(0.01)


def _release_lock(lock_file):
    """Release and close a lock file acquired by _acquire_lock."""
    if lock_file is None:
        return
    try:
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
    except OSError:
        pass
    lock_file.close()


def atomic_write_fleet_mode(path: str, data: dict, timeout: float = 5.0) -> None:
    """Atomically write fleet-mode.json using write-to-temp + os.rename.

    Steps:
      1. Validate schema (raises FleetModeSchemaError on failure)
      2. Acquire exclusive file lock (msvcrt.locking on Windows)
      3. Create temp file in same directory as target
      4. Write JSON to temp file, flush + fsync
      5. os.replace(temp, target) - atomic on POSIX and Windows (same volume)
      6. Release lock

    Args:
        path: target file path for fleet-mode.json
        data: dict conforming to fleet-mode schema
        timeout: max seconds to wait for lock (default 5.0)

    Raises:
        FleetModeSchemaError: if data fails validation
        TimeoutError: if lock cannot be acquired within timeout
        OSError: if filesystem operations fail
    """
    validate_fleet_mode(data)

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    lock_path = str(target) + ".lock"
    lock_file = _acquire_lock(lock_path, timeout=timeout)
    try:
        # Write to temp file in same directory (same filesystem for atomic rename)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(target.parent), prefix=".fleet_mode_", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            # Atomic rename (same directory = same volume on all supported OSes)
            os.replace(tmp_path, str(target))
        except BaseException:
            # Clean up temp file on any failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    finally:
        _release_lock(lock_file)


def read_fleet_mode(path: str) -> dict:
    """Safely read and validate fleet-mode.json.

    Returns the parsed dict. Raises FleetModeSchemaError or FileNotFoundError.
    """
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"fleet-mode file not found: {path}")
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    validate_fleet_mode(data)
    return data


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def selftest() -> bool:
    """Run comprehensive self-tests. Returns True if all pass."""
    import shutil
    test_dir = Path("memory/mechanic/fixtures/fleet_mode_infra_test")
    test_dir.mkdir(parents=True, exist_ok=True)
    target = test_dir / "fleet-mode.json"

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

    print("fleet_mode_infra.py selftest:")

    # Test 1: Valid write + read roundtrip
    valid_data = {
        "mode": "WORK",
        "timestamp": "2026-11-24T10:00:00Z",
        "goal_pct": 55.0,
        "agent_count": 7,
        "cycle": "cycle-15",
    }
    atomic_write_fleet_mode(str(target), valid_data)
    check("valid write creates file", target.exists())

    read_back = read_fleet_mode(str(target))
    check("read roundtrip mode", read_back["mode"] == "WORK")
    check("read roundtrip goal_pct", read_back["goal_pct"] == 55.0)
    check("read roundtrip agent_count", read_back["agent_count"] == 7)

    # Test 2: No temp files left behind
    leftover = list(test_dir.glob(".fleet_mode_*.tmp"))
    check("no temp files left after success", len(leftover) == 0)

    # Test 3: Invalid mode rejected
    try:
        atomic_write_fleet_mode(str(target), {"mode": "INVALID", "timestamp": "2026-11-24T10:00:00Z", "goal_pct": 50})
        check("invalid mode rejected", False)
    except FleetModeSchemaError:
        check("invalid mode rejected", True)

    # Test 4: Invalid timestamp rejected
    try:
        atomic_write_fleet_mode(str(target), {"mode": "WORK", "timestamp": "not-a-date", "goal_pct": 50})
        check("invalid timestamp rejected", False)
    except FleetModeSchemaError:
        check("invalid timestamp rejected", True)

    # Test 5: goal_pct out of range rejected
    try:
        atomic_write_fleet_mode(str(target), {"mode": "WORK", "timestamp": "2026-11-24T10:00:00Z", "goal_pct": 150})
        check("goal_pct >100 rejected", False)
    except FleetModeSchemaError:
        check("goal_pct >100 rejected", True)

    try:
        atomic_write_fleet_mode(str(target), {"mode": "WORK", "timestamp": "2026-11-24T10:00:00Z", "goal_pct": -5})
        check("goal_pct <0 rejected", False)
    except FleetModeSchemaError:
        check("goal_pct <0 rejected", True)

    # Test 6: Missing required field rejected
    try:
        atomic_write_fleet_mode(str(target), {"mode": "WORK"})
        check("missing timestamp+goal_pct rejected", False)
    except FleetModeSchemaError:
        check("missing timestamp+goal_pct rejected", True)

    # Test 7: All valid modes accepted
    for m in VALID_MODES:
        d = {"mode": m, "timestamp": "2026-11-24T12:00:00Z", "goal_pct": 80.0}
        atomic_write_fleet_mode(str(target), d)
        check(f"mode {m} accepted", read_fleet_mode(str(target))["mode"] == m)

    # Test 8: Concurrency - 10 threads write simultaneously, file must be valid JSON at end
    import threading
    errors = []
    def _worker(i):
        try:
            d = {"mode": "WORK", "timestamp": f"2026-11-24T10:{i:02d}:00Z", "goal_pct": float(i)}
            atomic_write_fleet_mode(str(target), d)
        except Exception as e:
            errors.append(e)
    threads = [threading.Thread(target=_worker, args=(i,)) for i in range(10)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=30)
    check("concurrent: no errors", len(errors) == 0)
    # File must be valid JSON after concurrent writes
    try:
        final = json.loads(target.read_text(encoding='utf-8'))
        check("concurrent: file is valid JSON", True)
        check("concurrent: mode is valid", final["mode"] in VALID_MODES)
    except (json.JSONDecodeError, KeyError):
        check("concurrent: file is valid JSON", False)
        check("concurrent: mode is valid", False)

    # Test 8b: Overwrite works (second write replaces first)
    atomic_write_fleet_mode(str(target), {"mode": "MAINTENANCE", "timestamp": "2026-11-24T13:00:00Z", "goal_pct": 95.0})
    check("overwrite works", read_fleet_mode(str(target))["mode"] == "MAINTENANCE")

    # Test 9: Non-dict input rejected
    try:
        atomic_write_fleet_mode(str(target), ["not", "a", "dict"])
        check("non-dict rejected", False)
    except FleetModeSchemaError:
        check("non-dict rejected", True)

    # Test 10: ISO-8601 with offset works
    atomic_write_fleet_mode(str(target), {"mode": "IDLE", "timestamp": "2026-11-24T14:30:00+05:30", "goal_pct": 100})
    check("ISO-8601 with offset accepted", read_fleet_mode(str(target))["mode"] == "IDLE")

    # Test 11: ISO-8601 with fractional seconds works
    atomic_write_fleet_mode(str(target), {"mode": "WORK", "timestamp": "2026-11-24T15:00:00.123Z", "goal_pct": 0})
    check("ISO-8601 fractional seconds accepted", read_fleet_mode(str(target))["goal_pct"] == 0)

    # Test 12: Concurrent-safe (write during read doesn't corrupt)
    # Simulate by writing and immediately reading
    atomic_write_fleet_mode(str(target), {"mode": "WORK", "timestamp": "2026-11-24T16:00:00Z", "goal_pct": 42.5})
    check("immediate read after write consistent", read_fleet_mode(str(target))["goal_pct"] == 42.5)

    # Test 13: File content is valid JSON (parse directly)
    with open(target, "r") as f:
        raw = json.load(f)
    check("file is valid standalone JSON", isinstance(raw, dict))

    # Cleanup
    shutil.rmtree(test_dir)

    print(f"\n  Result: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif "--write" in sys.argv:
        idx = sys.argv.index("--write")
        data_str = sys.argv[idx + 1]
        data = json.loads(data_str)
        target_path = "fleet-mode.json"
        if "--path" in sys.argv:
            pidx = sys.argv.index("--path")
            target_path = sys.argv[pidx + 1]
        atomic_write_fleet_mode(target_path, data)
        print(f"Wrote {target_path} (mode={data['mode']})")
    elif "--read" in sys.argv:
        target_path = "fleet-mode.json"
        if "--path" in sys.argv:
            pidx = sys.argv.index("--path")
            target_path = sys.argv[pidx + 1]
        data = read_fleet_mode(target_path)
        print(json.dumps(data, indent=2))
    else:
        print(__doc__)
        sys.exit(0)
