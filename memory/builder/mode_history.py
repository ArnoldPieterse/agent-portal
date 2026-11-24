"""Mode Transition History Logger - records every fleet-mode change to JSONL.

Feeds:
  - Archivist goal #2: Mode Transition Anomaly Log (raw data source)
  - Designer goal #4: Mode History Timeline (data source for UI)
  - Round topic: Fleet Autonomy Convergence (observability of mode changes)

Usage:
  python memory/builder/mode_history.py            # record current state (idempotent)
  python memory/builder/mode_history.py --summary  # print today's transitions
  python memory/builder/mode_history.py --selftest # verify all logic
"""
import json, os, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # project root
FLEET_MODE = ROOT / "fleet-mode.json"
HISTORY = ROOT / "memory" / "ops" / "mode-history.jsonl"

VALID_MODES = {"WORK", "MAINTENANCE", "IDLE"}


def _read_fleet_mode():
    """Read current fleet-mode.json. Returns dict or None."""
    try:
        return json.loads(FLEET_MODE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_last_entry():
    """Read the last line of mode-history.jsonl. Returns dict or None."""
    if not HISTORY.exists():
        return None
    try:
        lines = HISTORY.read_text(encoding="utf-8").strip().split("\n")
        if not lines or not lines[-1].strip():
            return None
        return json.loads(lines[-1])
    except (OSError, json.JSONDecodeError):
        return None


def _append_entry(record: dict):
    """Append a JSONL record atomically (write to temp + rename)."""
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    # Read existing content, append new line, write atomically
    existing = ""
    if HISTORY.exists():
        existing = HISTORY.read_text(encoding="utf-8")
        if existing and not existing.endswith("\n"):
            existing += "\n"
    new_content = existing + json.dumps(record, ensure_ascii=False) + "\n"
    # Atomic write: temp file in same dir + rename
    fd, tmp_path = tempfile.mkstemp(dir=str(HISTORY.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(new_content)
        os.replace(tmp_path, str(HISTORY))
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def record():
    """Main entry: detect mode change and append to history.
    
    Returns the new record dict if a change was detected, None if no change.
    """
    current = _read_fleet_mode()
    if current is None:
        return {"status": "no_fleet_mode", "recorded": False}

    last = _read_last_entry()
    
    # Determine if this is a new transition
    if last is not None:
        same_mode = last.get("mode") == current.get("mode")
        same_pct = abs(last.get("goal_pct", -1) - current.get("goal_pct", -1)) < 0.01
        same_ts = last.get("fleet_timestamp") == current.get("timestamp")
        if same_mode and same_pct and same_ts:
            return {"status": "no_change", "recorded": False}

    # Build the record
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "recorded_at": now_iso,
        "mode": current.get("mode"),
        "goal_pct": current.get("goal_pct"),
        "fleet_timestamp": current.get("timestamp"),
        "source": current.get("source", "unknown"),
        "previous_mode": last.get("mode") if last else None,
        "previous_goal_pct": last.get("goal_pct") if last else None,
    }
    _append_entry(record)
    return {"status": "recorded", "recorded": True, "entry": record}


def summary(days: int = 1):
    """Return transitions from the last N days. List of dicts."""
    if not HISTORY.exists():
        return []
    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    results = []
    for line in HISTORY.read_text(encoding="utf-8").strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            ts_str = entry.get("recorded_at", "")
            ts = datetime.fromisoformat(ts_str).timestamp()
            if ts >= cutoff:
                results.append(entry)
        except (json.JSONDecodeError, ValueError):
            continue
    return results


def _selftest():
    """Run self-test: verify record, summary, idempotency, schema."""
    import shutil
    test_hist = ROOT / "memory" / "ops" / "mode-history-selftest.jsonl"
    # Temporarily redirect HISTORY to a test file
    global HISTORY
    saved_history = HISTORY
    HISTORY = test_hist
    
    # Clean up any prior selftest file
    if test_hist.exists():
        test_hist.unlink()
    
    # Ensure fleet-mode.json exists with known state
    fm_backup = None
    if FLEET_MODE.exists():
        fm_backup = FLEET_MODE.read_text(encoding="utf-8")
    
    passed = 0
    failed = 0
    
    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")
    
    try:
        # Test 1: Initial record (no prior history)
        fm_data = {"mode": "WORK", "timestamp": "2026-11-24T10:00:00+00:00",
                   "goal_pct": 50.0, "source": "selftest", "schema_version": "1.0"}
        FLEET_MODE.write_text(json.dumps(fm_data), encoding="utf-8")
        result = record()
        check("T1 initial record created", result["recorded"] is True)
        check("T1 mode=WORK", result["entry"]["mode"] == "WORK")
        check("T1 previous_mode=None", result["entry"]["previous_mode"] is None)
        
        # Test 2: Idempotency - same state, no new record
        result2 = record()
        check("T2 idempotent (no change)", result2["recorded"] is False)
        
        # Test 3: Mode transition WORK -> MAINTENANCE
        fm_data["mode"] = "MAINTENANCE"
        fm_data["timestamp"] = "2026-11-24T11:00:00+00:00"
        FLEET_MODE.write_text(json.dumps(fm_data), encoding="utf-8")
        result3 = record()
        check("T3 transition recorded", result3["recorded"] is True)
        check("T3 previous_mode=WORK", result3["entry"]["previous_mode"] == "WORK")
        check("T3 mode=MAINTENANCE", result3["entry"]["mode"] == "MAINTENANCE")
        
        # Test 4: goal_pct change in same mode
        fm_data["goal_pct"] = 75.0
        FLEET_MODE.write_text(json.dumps(fm_data), encoding="utf-8")
        result4 = record()
        check("T4 pct change recorded", result4["recorded"] is True)
        
        # Test 5: Summary returns all entries
        entries = summary(days=1)
        check("T5 summary has 3 entries", len(entries) == 3)
        check("T5 first entry mode=WORK", entries[0]["mode"] == "WORK")
        check("T5 last entry pct=75.0", entries[-1]["goal_pct"] == 75.0)
        
        # Test 6: Atomic write - no temp files left
        tmps = list(HISTORY.parent.glob("mode-history-selftest.jsonl.tmp*")) + \
               list(HISTORY.parent.glob("*.tmp"))
        check("T6 no temp files left", len(tmps) == 0)
        
        # Test 7: Schema validation - all required fields present
        for e in entries:
            has_fields = all(k in e for k in ("recorded_at", "mode", "goal_pct", "fleet_timestamp"))
            check(f"T7 schema ok ({e['mode']})", has_fields)
            break  # just check one
        
        # Test 8: MAINTENANCE -> IDLE transition
        fm_data["mode"] = "IDLE"
        fm_data["timestamp"] = "2026-11-24T12:00:00+00:00"
        FLEET_MODE.write_text(json.dumps(fm_data), encoding="utf-8")
        result8 = record()
        check("T8 IDLE transition", result8["recorded"] is True)
        check("T8 prev=MAINTENANCE", result8["entry"]["previous_mode"] == "MAINTENANCE")
        
        # Test 9: No fleet-mode.json handling
        FLEET_MODE.unlink()
        result9 = record()
        check("T9 missing fm handled", result9["status"] == "no_fleet_mode")
        
    finally:
        HISTORY = saved_history
        if test_hist.exists():
            test_hist.unlink()
        # Restore fleet-mode.json
        if fm_backup is not None:
            FLEET_MODE.write_text(fm_backup, encoding="utf-8")
        elif FLEET_MODE.exists():
            pass  # leave as-is if we created it
    
    total = passed + failed
    print(f"\nSelf-test: {passed}/{total} PASS")
    return failed == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = _selftest()
        sys.exit(0 if ok else 1)
    elif "--summary" in sys.argv:
        entries = summary(days=1)
        if not entries:
            print("No mode transitions recorded in last 24h.")
        else:
            print(f"Mode transitions (last 24h): {len(entries)}")
            for e in entries:
                prev = e.get("previous_mode") or "(initial)"
                print(f"  {e['recorded_at'][:19]}  {prev} -> {e['mode']}  pct={e.get('goal_pct')}")
    else:
        result = record()
        if result["recorded"]:
            e = result["entry"]
            prev = e.get("previous_mode") or "(initial)"
            print(f"Recorded: {prev} -> {e['mode']} (pct={e.get('goal_pct')}) at {e['recorded_at'][:19]}")
        else:
            print(f"No change ({result['status']})")