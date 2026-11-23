#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""loop_stall_predictor.py - Researcher Goal 8 (cycle-11): Loop-Stall Predictor.

From an agent's recent activity (decision-log.jsonl + goal file evidence
stamps), compute a stall probability in [0,1]. Features are computable from
memory/ only (no network). Deterministic: same input -> same score.
Calibration target: productive sequences < 0.3, stalled > 0.7.

Usage:
  python loop_stall_predictor.py                 # all agents
  python loop_stall_predictor.py --agent NAME
  python loop_stall_predictor.py selftest
"""
import json, os, re, sys, time
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LOG = os.path.join(ROOT, "decision-log.jsonl")
GOALS = os.path.join(ROOT, "memory", "goals")
AGENTS = ["archivist", "builder", "designer", "mechanic", "orchestrator",
          "researcher", "scribe", "verifier"]


def _parse_ts(t):
    try:
        return datetime.fromisoformat(str(t).replace("Z", "+00:00"))
    except Exception:
        return None


def agent_features(name, now=None):
    now = now or datetime.now(timezone.utc)
    entries = []
    if os.path.exists(LOG):
        for line in open(LOG, encoding="utf-8", errors="replace"):
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(e.get("agent", "")).lower() != name.lower():
                continue
            ts = _parse_ts(e.get("ts") or e.get("timestamp"))
            if ts:
                entries.append(ts)
    gp = os.path.join(GOALS, name + ".md")
    n_goals = 0
    n_done = 0
    if os.path.exists(gp):
        for line in open(gp, encoding="utf-8", errors="replace"):
            if re.match(r"^\s*\d+[.)]", line) or re.match(r"^\s*[-*]\s*\[[ xX]\]", line):
                n_goals += 1
                if "verified:" in line or "recorded" in line:
                    n_done += 1
    last = max(entries) if entries else None
    idle_h = (now - last).total_seconds() / 3600.0 if last else 999.0
    recent_24h = sum(1 for t in entries if now - t <= timedelta(hours=24))
    return {
        "agent": name,
        "idle_hours": round(idle_h, 2),
        "actions_24h": recent_24h,
        "total_actions": len(entries),
        "goals_total": n_goals,
        "goals_done": n_done,
    }


def stall_probability(f):
    """Hand-tuned logistic over memory-computable features (documented weights).

    idle_hours:      log-scale saturation at ~48h            w=+0.9
    actions_24h:     0 actions pushes up, >=3 saturates down w=-0.5 each
    goal progress:   open-goal ratio mildly informative       w=+0.2
    """
    import math
    z = 0.0
    z += 0.9 * min(1.0, math.log1p(max(0.0, f["idle_hours"])) / math.log(49.0))
    z -= 0.5 * min(3, f["actions_24h"])
    if f["goals_total"]:
        z += 0.2 * (f["goals_total"] - f["goals_done"]) / float(f["goals_total"])
    return round(1.0 / (1.0 + math.exp(-z)), 4)


def predict(names=None, now=None):
    out = []
    for name in (names or AGENTS):
        f = agent_features(name, now)
        p = stall_probability(f)
        f["stall_probability"] = p
        f["verdict"] = "stalled" if p > 0.7 else ("at_risk" if p >= 0.3 else "productive")
        out.append(f)
    return sorted(out, key=lambda x: -x["stall_probability"])


def selftest():
    now = datetime(2026, 11, 23, 9, 0, tzinfo=timezone.utc)
    # productive fixture: recent actions, goals closing
    prod = {"agent": "t", "idle_hours": 0.5, "actions_24h": 5,
            "total_actions": 50, "goals_total": 10, "goals_done": 8}
    # stalled fixture: silent for days, nothing done
    stall = {"agent": "t", "idle_hours": 72.0, "actions_24h": 0,
             "total_actions": 5, "goals_total": 10, "goals_done": 0}
    pp, ps = stall_probability(prod), stall_probability(stall)
    assert pp < 0.3, "productive sequence scored %.3f (want <0.3)" % pp
    assert ps > 0.7, "stalled sequence scored %.3f (want >0.7)" % ps
    # determinism
    assert stall_probability(stall) == ps
    # live pass runs and stays in [0,1]
    rows = predict(None, now)
    assert len(rows) == len(AGENTS)
    for r in rows:
        assert 0.0 <= r["stall_probability"] <= 1.0
    print("fixtures: productive=%.3f stalled=%.3f | live top=%s %.3f"
          % (pp, ps, rows[0]["agent"], rows[0]["stall_probability"]))
    print("SELFTEST PASS")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        selftest()
    elif len(sys.argv) > 2 and sys.argv[1] == "--agent":
        print(json.dumps(predict([sys.argv[2]]), indent=1))
    else:
        for r in predict():
            print("%-14s p=%.3f %-10s idle=%sh actions24h=%d goals=%d/%d"
                  % (r["agent"], r["stall_probability"], r["verdict"],
                     r["idle_hours"], r["actions_24h"], r["goals_done"], r["goals_total"]))

