#!/usr/bin/env python3
"""mode_schema_check.py - Standalone schema validator for fleet-mode.json (Verifier cycle-15 G3).

Runs on every mode write: memory/builder/fleet_mode_writer.write_mode() calls
validate_fleet_mode() as a second validation layer (in addition to the writer's own
validate()). Any error is logged before the write proceeds.

Schema (memory/ops/fleet-mode.json):
  mode           one of {WORK, MAINTENANCE, IDLE}
  timestamp      ISO-8601 string (required)
  goal_pct       number in [0, 100] (validated when present; bools rejected)
  last_activity  ISO-8601 string (validated when present)

CLI:
  python mode_schema_check.py <file.json>   # validate a file, exit 0/1
  python mode_schema_check.py selftest      # corrupt each field individually, all must fail
"""
import json
import os
import sys
import time
from datetime import datetime

MODES = ("WORK", "MAINTENANCE", "IDLE")
HERE = os.path.dirname(os.path.abspath(__file__))          # memory/verifier
BASE = os.path.abspath(os.path.join(HERE, "..", ".."))
DEFAULT_FILE = os.path.join(BASE, "memory", "ops", "fleet-mode.json")
LOG_FILE = os.path.join(BASE, "memory", "ops", "mode-schema-errors.log")


def _iso_ok(v) -> bool:
    if not isinstance(v, str) or not v:
        return False
    try:
        datetime.fromisoformat(v.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_fleet_mode(payload) -> list:
    """Return a list of schema errors (empty list == valid)."""
    errs = []
    if not isinstance(payload, dict):
        return [f"payload must be an object, got {type(payload).__name__}"]
    mode = payload.get("mode")
    if mode not in MODES:
        errs.append(f"mode must be one of {list(MODES)}, got {mode!r}")
    ts = payload.get("timestamp")
    if not _iso_ok(ts):
        errs.append(f"timestamp must be a non-empty ISO-8601 string, got {ts!r}")
    gp = payload.get("goal_pct")
    if gp is not None:
        if isinstance(gp, bool) or not isinstance(gp, (int, float)):
            errs.append(f"goal_pct must be a number, got {type(gp).__name__}")
        elif not (0 <= gp <= 100):
            errs.append(f"goal_pct must be in [0, 100], got {gp!r}")
    la = payload.get("last_activity")
    if la is not None and not _iso_ok(la):
        errs.append(f"last_activity must be ISO-8601 when present, got {la!r}")
    return errs


def validate_file(path: str = DEFAULT_FILE) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, ValueError) as e:
        return [f"cannot read/parse {os.path.basename(path)}: {e}"]
    return validate_fleet_mode(payload)


def log_errors(errs: list, source: str = "") -> None:
    """Append validation errors to the ops error log (called by write_mode on failure)."""
    if not errs:
        return
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            for e in errs:
                f.write(f"{datetime.utcnow().isoformat()}Z mode_schema_check {source} {e}\n")
    except OSError:
        pass


def selftest() -> int:
    good = {"mode": "MAINTENANCE", "timestamp": "2026-11-24T11:00:00+00:00",
            "goal_pct": 100.0, "last_activity": "2026-11-24T10:59:00+00:00"}
    t0 = time.perf_counter()
    assert validate_fleet_mode(good) == [], validate_fleet_mode(good)

    cases = [
        ("mode", {**good, "mode": "SLEEPING"}, "mode must be one of"),
        ("mode-missing", {k: v for k, v in good.items() if k != "mode"}, "mode must be one of"),
        ("timestamp-bad", {**good, "timestamp": "yesterday"}, "timestamp must be a non-empty ISO-8601"),
        ("timestamp-missing", {k: v for k, v in good.items() if k != "timestamp"}, "timestamp must be a non-empty ISO-8601"),
        ("goal_pct-high", {**good, "goal_pct": 142.0}, "goal_pct must be in [0, 100]"),
        ("goal_pct-negative", {**good, "goal_pct": -5}, "goal_pct must be in [0, 100]"),
        ("goal_pct-bool", {**good, "goal_pct": True}, "goal_pct must be a number"),
        ("last_activity-bad", {**good, "last_activity": "not-a-date"}, "last_activity must be ISO-8601"),
    ]
    for name, payload, needle in cases:
        errs = validate_fleet_mode(payload)
        assert errs and any(needle in e for e in errs), (name, errs)

    # non-dict payload
    assert any("must be an object" in e for e in validate_fleet_mode([1, 2]))

    # live file validates clean (or the error is real and gets reported)
    live = validate_file(DEFAULT_FILE) if os.path.exists(DEFAULT_FILE) else []
    dt_ms = (time.perf_counter() - t0) * 1000.0
    assert dt_ms < 100, f"selftest took {dt_ms:.1f}ms (>100ms)"
    print(f"SELFTEST OK ({len(cases)} corrupted-field cases + valid case; live file: "
          f"{'clean' if not live else live}; {dt_ms:.1f}ms < 100ms)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(selftest())
    errs = validate_file(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE)
    print(json.dumps(errs, indent=2))
    sys.exit(1 if errs else 0)
