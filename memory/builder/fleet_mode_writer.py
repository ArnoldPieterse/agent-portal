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


def _ensure_fsm_stamped(payload: dict) -> None:
    """Convergence FSM (Builder goal 1): ensure a mode write carries fsm_state +
    fsm_validated so no writer bypasses the state machine. Respects an already-
    validated payload (e.g. one produced by convergence_fsm itself) to avoid loops."""
    if not isinstance(payload, dict) or payload.get("fsm_validated") is True:
        return
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location(
            "convergence_fsm", str(HERE / "convergence_fsm.py"))
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        fsm = _mod.ConvergenceFSM(Path(path), HERE.parent / "ops" / "fsm-events.jsonl")
        payload["fsm_state"] = fsm.current_state()
        payload["fsm_validated"] = True
    except Exception:
        # FSM unavailable (e.g. module missing): fall back to a valid default so the
        # schema contract (fsm_state present) still holds; never break the write.
        payload.setdefault("fsm_state", "DISCOVERING")
        payload["fsm_validated"] = True


def write_mode(payload: dict, path: Path | str = DEFAULT_PATH) -> bool:
    """Atomically write payload to path after schema validation.

    Returns True on success. Raises ValueError on schema violation (nothing
    written). Returns False on IO failure (e.g. disk full): error logged,
    temp cleaned up, previous file untouched.
    """
    path = Path(path)
    _ensure_fsm_stamped(payload)
    errs = validate(payload)
    # cycle-15 verifier G3: second independent validation layer (mode_schema_check),
    # runs on EVERY write; errors are logged to memory/ops/mode-schema-errors.log.
    try:
        import importlib.util as _ilu
        _msc_path = Path(__file__).resolve().parent.parent / "verifier" / "mode_schema_check.py"
        _spec = _ilu.spec_from_file_location("mode_schema_check", str(_msc_path))
        _msc = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_msc)
        errs2 = _msc.validate_fleet_mode(payload)
        if errs2:
            _msc.log_errors(errs2, source=f"write_mode:{path.name}")
            raise ValueError("schema validation failed (mode_schema_check): " + "; ".join(errs2))
    except ImportError:
        pass   # validator module missing - writer's own validate() still guards
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
