#!/usr/bin/env python3
"""Circuit breaker for auto-remediation (Mechanic cycle-10 goal 4).

Tracks consecutive auto-remediation failures per host. After FAIL_LIMIT (3)
consecutive failures on the same host, ALL auto-actions on that host halt and
the host is marked "MANUAL REVIEW" (surfaced in /api/fleet/cockpit). The break
event is logged to memory/ops/decision-log.jsonl. A successful manual
intervention (manual_reset) or a later successful auto-remediation clears it.

State: memory/mechanic/.circuit_breaker_state.json
  {host: {"consecutive_fails": int, "open": bool, "broke_at": iso|None}}
"""
import json, os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, ".circuit_breaker_state.json")
DECISION_LOG = os.path.normpath(os.path.join(HERE, "..", "..", "memory", "ops", "decision-log.jsonl"))
FAIL_LIMIT = 3

def _now():
    return datetime.now(timezone.utc).isoformat()

def _load(path=None):
    p = path or STATE_FILE
    try:
        return json.loads(open(p, encoding="utf-8").read())
    except (OSError, ValueError):
        return {}

def _save(state, path=None):
    p = path or STATE_FILE
    open(p, "w", encoding="utf-8").write(json.dumps(state, indent=2))

def _log_event(host, kind, detail):
    try:
        e = {"ts": _now(), "agent": "mechanic", "kind": "circuit_breaker",
             "host": host, "event": kind, "detail": detail}
        with open(DECISION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(e) + "\n")
    except OSError:
        pass

def record_attempt(host, success, path=None):
    """Record one auto-remediation attempt on `host`. Returns the new state of
    the circuit plus an `action` hint: CONTINUE / HALT_AUTO_ACTIONS / RESET."""
    st = _load(path)
    h = st.setdefault(str(host), {"consecutive_fails": 0, "open": False, "broke_at": None})
    if success:
        was_open = h["open"]
        h.update(consecutive_fails=0, open=False, broke_at=None)
        action = "RESET" if was_open else "CONTINUE"
        if was_open:
            _log_event(host, "circuit_closed", "successful auto-remediation after break")
    else:
        h["consecutive_fails"] += 1
        action = "CONTINUE"
        if h["consecutive_fails"] >= FAIL_LIMIT and not h["open"]:
            h["open"] = True
            h["broke_at"] = _now()
            action = "HALT_AUTO_ACTIONS"
            _log_event(host, "circuit_broken",
                       "%d consecutive auto-remediation failures - host marked MANUAL REVIEW" % h["consecutive_fails"])
    _save(st, path)
    return {"host": str(host), "consecutive_fails": h["consecutive_fails"],
            "open": h["open"], "action": action}

def is_halted(host, path=None):
    """True if auto-actions must NOT run on this host right now."""
    h = _load(path).get(str(host))
    return bool(h and h.get("open"))

def manual_reset(host, by="human", path=None):
    """Successful manual intervention: clear the circuit on `host`."""
    st = _load(path)
    h = st.get(str(host))
    if h is None:
        return {"host": str(host), "reset": False, "reason": "no state"}
    was_open = bool(h.get("open"))
    h.update(consecutive_fails=0, open=False, broke_at=None)
    _save(st, path)
    if was_open:
        _log_event(host, "circuit_reset", "manual intervention by %s" % by)
    return {"host": str(host), "reset": True, "was_open": was_open}

def status(path=None):
    """Cockpit view: {host: {"state": OK|WATCH|MANUAL REVIEW, consecutive_fails, broke_at}}."""
    out = {}
    for host, h in _load(path).items():
        if h.get("open"):
            s = "MANUAL REVIEW"
        elif h.get("consecutive_fails", 0) >= FAIL_LIMIT - 1:
            s = "WATCH"
        else:
            s = "OK"
        out[host] = {"state": s, "consecutive_fails": h.get("consecutive_fails", 0),
                     "broke_at": h.get("broke_at")}
    return out

if __name__ == "__main__":
    import tempfile
    tmp = tempfile.mkdtemp(prefix="cb_test_")
    sp = os.path.join(tmp, "state.json")
    DECISION_LOG = os.path.join(tmp, "log.jsonl")
    fails = []
    for i in range(2):
        r = record_attempt("Red", False, path=sp)
        assert r["action"] == "CONTINUE" and not is_halted("Red", sp), r
    r = record_attempt("Red", False, path=sp)
    assert r["action"] == "HALT_AUTO_ACTIONS" and is_halted("Red", sp), r
    assert status(sp)["Red"]["state"] == "MANUAL REVIEW"
    r = record_attempt("Red", True, path=sp)
    assert r["action"] == "RESET" and not is_halted("Red", sp), r
    for i in range(3):
        record_attempt("Red", False, path=sp)
    assert is_halted("Red", sp)
    m = manual_reset("Red", by="self-test", path=sp)
    assert m["reset"] and m["was_open"] and not is_halted("Red", sp), m
    lines = [json.loads(l) for l in open(DECISION_LOG, encoding="utf-8")]
    kinds = [e["event"] for e in lines]
    assert "circuit_broken" in kinds and "circuit_reset" in kinds, kinds
    print("SELF-TEST PASS: break@%d fails, halt, auto-reset, manual-reset, %d log events"
          % (FAIL_LIMIT, len(lines)))
