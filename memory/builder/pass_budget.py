#!/usr/bin/env python3
"""pass_budget.py - Fleet-wide pass budget with IDLE handoff on exhaustion.

Builds: builder goal 8 (Pass Budget Enforcer).
State: memory/ops/pass-budget.json -> {"used": int, "total": int}

Behavior:
  acquire() is called once per dispatch. It atomically increments `used`.
  When used reaches total it returns budget_exhausted=True and flips the
  fleet to IDLE mode through fleet_mode_writer (best-effort; a writer
  failure is logged, never fatal).
  Once exhausted, further acquire() calls return granted=False WITHOUT
  incrementing the counter - dispatch receives no tasks until reset().

Events are appended to memory/ops/pass-budget-events.jsonl for auditing.

CLI:
  python pass_budget.py state                 # current budget state
  python pass_budget.py acquire               # one dispatch (prints result)
  python pass_budget.py reset [--total 200]   # new cycle/day budget
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parent / "ops"
BUDGET_FILE = OPS / "pass-budget.json"
EVENTS_FILE = OPS / "pass-budget-events.jsonl"
DEFAULT_TOTAL = 200

_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_event(event: str, **kw) -> None:
    rec = {"ts": _now(), "event": event}
    rec.update(kw)
    try:
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError:
        pass


def _goal_pct() -> float | None:
    """Best-effort fleet goal % from the researcher ledger (None on any error)."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "gl", HERE.parent / "researcher" / "goal_ledger.py")
        gl = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gl)
        goals_dir = HERE.parent / "goals"
        done = total = 0
        for fn in sorted(goals_dir.glob("*.md")):
            if fn.name.startswith(("_", ".")) or fn.name.upper() == "README.MD":
                continue
            for g in gl.parse_agent_file(str(fn)):
                total += 1
                if g["status"] == "reached":
                    done += 1
        return round(100.0 * done / total, 1) if total else None
    except Exception:
        return None


def _idle_mode_write() -> bool:
    """Flip fleet to IDLE via the atomic writer; returns success."""
    try:
        from fleet_mode_writer import write_mode
        payload = {"mode": "IDLE", "timestamp": _now(),
                   "trigger": "pass_budget_exhausted"}
        pct = _goal_pct()
        if pct is not None:
            payload["goal_pct"] = pct
        return write_mode(payload)
    except Exception as e:  # noqa: BLE001 - budget logic must survive writer issues
        try:
            _log_event("idle_write_failed", error=str(e)[:200])
        except Exception:
            pass
        return False


def load_state(path: Path | str = BUDGET_FILE) -> dict:
    p = Path(path)
    if not p.exists():
        return {"used": 0, "total": DEFAULT_TOTAL}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return {"used": int(d.get("used", 0)), "total": int(d.get("total", DEFAULT_TOTAL))}
    except (json.JSONDecodeError, ValueError, TypeError):
        return {"used": 0, "total": DEFAULT_TOTAL}


def state(path: Path | str = BUDGET_FILE) -> dict:
    s = load_state(path)
    s["exhausted"] = s["used"] >= s["total"]
    s["remaining"] = max(0, s["total"] - s["used"])
    return s


def acquire(path: Path | str = BUDGET_FILE) -> dict:
    """One dispatch. Increments unless already exhausted (then no increment)."""
    with _lock:
        s = load_state(path)
        if s["used"] >= s["total"]:
            out = {"granted": False, "budget_exhausted": True,
                   "used": s["used"], "total": s["total"]}
            _log_event("noop_exhausted", **{k: out[k] for k in ("used", "total")})
            return out
        s["used"] += 1
        p = Path(path)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(s), encoding="utf-8")
        tmp.replace(p)
        exhausted = s["used"] >= s["total"]
        out = {"granted": True, "budget_exhausted": exhausted,
               "used": s["used"], "total": s["total"]}
        if exhausted:
            ok = _idle_mode_write()
            _log_event("exhausted", idle_mode_written=ok, **{k: out[k] for k in ("used", "total")})
        else:
            _log_event("increment", **{k: out[k] for k in ("used", "total")})
        return out


def reset(total: int = DEFAULT_TOTAL, path: Path | str = BUDGET_FILE) -> dict:
    with _lock:
        s = {"used": 0, "total": int(total)}
        p = Path(path)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(s), encoding="utf-8")
        tmp.replace(p)
        _log_event("reset", used=0, total=s["total"])
        return s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("state")
    sub.add_parser("acquire")
    r = sub.add_parser("reset")
    r.add_argument("--total", type=int, default=DEFAULT_TOTAL)
    args = ap.parse_args()
    if args.cmd == "reset":
        print(json.dumps(reset(args.total)))
    elif args.cmd == "acquire":
        print(json.dumps(acquire()))
    else:
        print(json.dumps(state(), indent=2))
