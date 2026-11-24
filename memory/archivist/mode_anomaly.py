#!/usr/bin/env python3
"""mode_anomaly.py - Log fleet mode transitions and flag forecast deviations (archivist).

- detect(): compares memory/ops/fleet-mode.json against last-seen state; on change,
  appends {ts, from, to} to memory/ops/mode-transitions.jsonl.
- forecast(target_mode, expected_time_iso, context): records an expectation in
  memory/ops/mode-forecasts.jsonl (id auto).
- evaluate(now=None): resolves forecasts against the transition log; any realized
  transition deviating >30 min from expectation is logged to
  memory/archivist/mode-anomalies.jsonl. Unresolved forecasts older than their
  expected time + 30 min are flagged 'pending_late' once.

CLI: python mode_anomaly.py [detect|evaluate|forecast <mode> <iso> <ctx>|selftest]
"""
import json, os, sys, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
MODE_FILE = BASE / "memory" / "ops" / "fleet-mode.json"
LAST_SEEN = BASE / "memory" / "ops" / "mode-last-seen.json"
TRANSITIONS = BASE / "memory" / "ops" / "mode-transitions.jsonl"
FORECASTS = BASE / "memory" / "ops" / "mode-forecasts.jsonl"
ANOMALIES = BASE / "memory" / "archivist" / "mode-anomalies.jsonl"
THRESHOLD_MIN = 30


def _now():
    return datetime.now(timezone.utc)


def _ts(dt=None):
    return (dt or _now()).isoformat()


def _read_mode():
    try:
        d = json.loads(MODE_FILE.read_text(encoding="utf-8"))
        return d.get("mode") if isinstance(d, dict) else None
    except Exception:
        return None


def _append(path, rec):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def detect():
    cur = _read_mode()
    if cur is None:
        return None
    prev = None
    if LAST_SEEN.exists():
        try:
            prev = json.loads(LAST_SEEN.read_text(encoding="utf-8")).get("mode")
        except Exception:
            prev = None
    LAST_SEEN.write_text(json.dumps({"mode": cur, "seen_at": _ts()}), encoding="utf-8")
    if prev is not None and prev != cur:
        rec = {"ts": _ts(), "from": prev, "to": cur}
        _append(TRANSITIONS, rec)
        return rec
    return None


def forecast(target_mode, expected_time_iso, context=""):
    try:
        datetime.fromisoformat(expected_time_iso)
    except Exception:
        raise ValueError("expected_time must be ISO-8601")
    rec = {"id": uuid.uuid4().hex[:8], "target_mode": target_mode,
           "expected_time": expected_time_iso, "context": context,
           "created_at": _ts(), "resolved": False}
    _append(FORECASTS, rec)
    return rec["id"]


def _transitions():
    out = []
    if TRANSITIONS.exists():
        for ln in TRANSITIONS.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def evaluate(now=None):
    now = now or _now()
    events = _transitions()
    if not FORECASTS.exists():
        return []
    lines = [json.loads(l) for l in FORECASTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    new_anoms = []
    changed = False
    for fc in lines:
        if fc.get("resolved"):
            continue
        try:
            exp = datetime.fromisoformat(fc["expected_time"])
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        created = None
        try:
            created = datetime.fromisoformat(fc["created_at"])
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
        except Exception:
            pass
        hit = None
        for ev in events:
            try:
                t = datetime.fromisoformat(ev["ts"])
                if t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
            except Exception:
                continue
            ok_time = created is None or t >= created - timedelta(minutes=5)
            if ev.get("to") == fc.get("target_mode") and ok_time:
                hit = (t, ev); break
        dev_min = None
        kind = None
        if hit:
            t, ev = hit
            dev_min = round(abs((t - exp).total_seconds()) / 60.0, 1)
            fc["resolved"] = True; changed = True
            if dev_min > THRESHOLD_MIN:
                kind = "deviation"
        elif now >= exp + timedelta(minutes=THRESHOLD_MIN):
            fc["resolved"] = True; fc["late_logged"] = True; changed = True
            dev_min = round((now - exp).total_seconds() / 60.0, 1)
            kind = "pending_late"
        if kind:
            rec = {"forecast_id": fc["id"], "target_mode": fc.get("target_mode"),
                   "expected_time": fc["expected_time"], "kind": kind,
                   "deviation_min": dev_min, "context": fc.get("context", ""),
                   "logged_at": _ts(now)}
            _append(ANOMALIES, rec); new_anoms.append(rec)
    if changed:
        FORECASTS.write_text("\n".join(json.dumps(f) for f in lines) + "\n", encoding="utf-8")
    return new_anoms


def selftest():
    import tempfile, shutil
    tmp = Path(tempfile.mkdtemp(prefix="modean_"))
    try:
        g = sys.modules[__name__]
        real = (g.MODE_FILE, g.LAST_SEEN, g.TRANSITIONS, g.FORECASTS, g.ANOMALIES)
        ops = tmp / "ops"; arch = tmp / "arch"
        g.MODE_FILE, g.LAST_SEEN, g.TRANSITIONS, g.FORECASTS, g.ANOMALIES = (
            ops / "fleet-mode.json", ops / "last.json", ops / "trans.jsonl",
            ops / "fc.jsonl", arch / "anom.jsonl")
        from datetime import timedelta
        t0 = _now()
        ops.mkdir(parents=True, exist_ok=True); arch.mkdir(parents=True)
        g.MODE_FILE.write_text(json.dumps({"mode": "normal"}))
        assert g.detect() is None
        g.MODE_FILE.write_text(json.dumps({"mode": "recovery"}))
        rec = g.detect(); assert rec and rec["from"] == "normal" and rec["to"] == "recovery", rec
        # forecast 1: +45 min late -> deviation; forecast 2: -35 min early -> deviation;
        # forecast 3: +10 min -> ok, no anomaly; forecast 4: never comes -> pending_late
        f1 = g.forecast("recovery", (t0 + timedelta(minutes=45)).isoformat(), "late")
        f2 = g.forecast("normal", (t0 - timedelta(minutes=35)).isoformat(), "early")
        f3 = g.forecast("recovery", (t0 + timedelta(minutes=10)).isoformat(), "ok")
        f4 = g.forecast("hibernate", (t0 - timedelta(hours=2)).isoformat(), "never")
        # transition 'recovery' happened at ~t0; add a 'normal' transition 35 min early of exp
        _append(g.TRANSITIONS, {"ts": (t0 + timedelta(minutes=1)).isoformat(), "from": "recovery", "to": "normal"})
        anoms = g.evaluate(now=t0 + timedelta(hours=3))
        kinds = {a["forecast_id"]: a for a in anoms}
        assert f1 in kinds and kinds[f1]["kind"] == "deviation" and abs(kinds[f1]["deviation_min"] - 45) < 2, kinds.get(f1)
        assert f2 in kinds and kinds[f2]["kind"] == "deviation", kinds.get(f2)
        assert f3 not in kinds, kinds.get(f3)
        assert f4 in kinds and kinds[f4]["kind"] == "pending_late", kinds.get(f4)
        # idempotent: second evaluate produces nothing new
        assert g.evaluate(now=t0 + timedelta(hours=3)) == []
        print("SELFTEST OK")
    finally:
        g.MODE_FILE, g.LAST_SEEN, g.TRANSITIONS, g.FORECASTS, g.ANOMALIES = real
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    a = sys.argv[1:] if len(sys.argv) > 1 else ["detect"]
    try:
        if a[0] == "selftest":
            selftest()
        elif a[0] == "detect":
            print(json.dumps(detect()))
        elif a[0] == "evaluate":
            print(json.dumps(evaluate()))
        elif a[0] == "forecast" and len(a) >= 3:
            print(forecast(a[1], a[2], a[3] if len(a) > 3 else ""))
        else:
            print("usage: detect|evaluate|forecast <mode> <iso> [ctx]|selftest"); sys.exit(2)
    except Exception as e:
        print("ERROR:", e); sys.exit(1)
