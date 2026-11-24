#!/usr/bin/env python3
"""fleet_mode_writer.py - Atomic, schema-validated writer for memory/ops/fleet-mode.json.

Builds: builder goal 3 (fleet-mode.json Atomic Writer) + mechanic goal 1 (Infra).

Guarantees:
  * Atomic write: temp file in same directory + os.replace (atomic on NTFS).
  * Schema validation BEFORE any write: mode in {WORK, MAINTENANCE, IDLE},
    timestamp ISO-8601, goal_pct a number in 0..100. Bad payloads are
    rejected with ValueError and never touch disk.
  * Disk-full / IO failure: error is logged to memory/ops/fleet-mode-writer.log,
    the temp file is removed, and the PREVIOUS fleet-mode.json stays intact
    (rename never happens on a failed write).
  * Concurrent-safe: process-local lock + unique temp names; N concurrent
    writers each produce a valid final JSON file.

CLI:
  python fleet_mode_writer.py validate [path]      # check a file, exit 0/1
  python fleet_mode_writer.py set MODE --goal-pct F [--total N --reached N]
"""
from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent            # memory/builder
OPS = HERE.parent / "ops"
DEFAULT_PATH = OPS / "fleet-mode.json"
LOG_PATH = OPS / "fleet-mode-writer.log"
MODES = ("WORK", "MAINTENANCE", "IDLE")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [fleet_mode_writer] %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger("fleet_mode_writer")

_LOCK = threading.Lock()


def validate(payload) -> list[str]:
    """Return a list of schema errors (empty list == valid)."""
    errs: list[str] = []
    if not isinstance(payload, dict):
        return [f"payload must be an object, got {type(payload).__name__}"]
    mode = payload.get("mode")
    if mode not in MODES:
        errs.append(f"mode must be one of {list(MODES)}, got {mode!r}")
    ts = payload.get("timestamp")
    if not isinstance(ts, str) or not ts:
        errs.append("timestamp must be a non-empty ISO-8601 string")
    else:
        try:
            datetime.fromisoformat(ts)
        except ValueError:
            errs.append(f"timestamp is not valid ISO-8601: {ts!r}")
    gp = payload.get("goal_pct")
    if gp is not None:
        if isinstance(gp, bool) or not isinstance(gp, (int, float)):
            errs.append(f"goal_pct must be a number, got {type(gp).__name__}")
        elif not (0 <= float(gp) <= 100):
            errs.append(f"goal_pct out of range 0..100: {gp!r}")
    return errs


def write_mode(payload: dict, path: Path | str = DEFAULT_PATH) -> bool:
    """Atomically write payload to path after schema validation.

    Returns True on success. Raises ValueError on schema violation (nothing
    written). Returns False on IO failure (e.g. disk full): error logged,
    temp cleaned up, previous file untouched.
    """
    path = Path(path)
    errs = validate(payload)
    if errs:
        raise ValueError("schema validation failed: " + "; ".join(errs))
    with _LOCK:
        fd, tmp = tempfile.mkstemp(prefix=".fleet-mode-", suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, str(path))   # atomic on NTFS
        except OSError as e:
            # Disk full / permission / anything: never corrupt the live file.
            try:
                if os.path.exists(tmp):
                    os.unlink(tmp)
            except OSError:
                pass
            log.error("write failed (%s); previous %s left intact", e, path.name)
            return False
        return True


def read_mode(path: Path | str = DEFAULT_PATH) -> dict | None:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def set_mode(mode: str, goal_pct: float | None = None, **extra) -> bool:
    """Convenience: build a full payload from the current file + overrides."""
    cur = read_mode() or {}
    payload = {
        "mode": mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal_pct": goal_pct if goal_pct is not None else cur.get("goal_pct"),
    }
    for k in ("goals_total", "goals_reached", "goals_open"):
        if k in extra:
            payload[k] = extra[k]
        elif k in cur:
            payload[k] = cur[k]
    payload.update({k: v for k, v in extra.items() if k not in ("goals_total", "goals_reached", "goals_open")})
    return write_mode(payload)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "validate":
        p = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PATH
        data = json.loads(p.read_text(encoding="utf-8"))
        e = validate(data)
        print("OK" if not e else "INVALID: " + "; ".join(e))
        sys.exit(0 if not e else 1)
    elif len(sys.argv) >= 3 and sys.argv[1] == "set":
        m = sys.argv[2]
        pct = float(sys.argv[3]) if len(sys.argv) > 3 else None
        ok = set_mode(m, pct)
        print("written" if ok else "FAILED (see log)")
        sys.exit(0 if ok else 1)
    else:
        print(__doc__)
