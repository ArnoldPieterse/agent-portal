#!/usr/bin/env python3
"""Planned-work layer over next10.json (2026-11-24, Orchestrator seat).

next10.json says HOW the forecast works; this module answers WHAT is planned:
  - per horizon: which goals are planned to complete, expected outcome, and WHY each
  - when the fleet is all-clear (next10 empty): projects the NEXT cycle from the
    ranked backlog candidates, so every horizon always carries concrete planned work
  - a decision tree: state -> gate (all goals 100%?) -> level-up + new cycle | keep queue

Stdlib only. Used by make_forecast_deck.py and forecast_engine._write_outputs.
"""
import json
import os
import re
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
HORIZONS = [("30m", 0.5), ("1h", 1.0), ("1d", 24.0), ("1w", 168.0), ("1m", 720.0)]
TYPE_PAT = [
    ("verify",      re.compile(r"(?i)\b(verify|validation|benchmark|regression test|audit|consistency check|compliance)\b")),
    ("research",    re.compile(r"(?i)\b(research|detector|matcher|anomaly|conflict|pattern|precedent|analysis)\b")),
    ("measurement", re.compile(r"(?i)\b(measure|monitor|heatmap|scoring|track|score|histogram|benchmark suite)\b")),
    ("ops",         re.compile(r"(?i)\b(schtask|deploy|runbook|maintenance window|recovery|heal|lifecycle|arbitration)\b")),
]
BASE_HOURS = {"build": 4.0, "verify": 2.0, "research": 5.0, "measurement": 3.0, "ops": 2.0}
COMPLEX_MULT = {1: 1.0, 2: 1.6, 3: 2.5}


def _classify(text):
    for t, p in TYPE_PAT:
        if p.search(text):
            return t
    return "build"


def _complexity(text):
    crit = text.count("; ") + (1 if re.search(r"(?i)verified\s*:", text) else 0)
    files = len(re.findall(r"`[^`]+\.py`|/api/[a-z/]+", text))
    score = min(crit, 3) + min(files, 2)
    return max(1, min(3, 1 + (score >= 3)))


def _steps_for(gtype):
    base = {
        "build":       ["scaffold module", "implement core logic", "self-test until AC green", "evidence leaf + index line"],
        "verify":      ["build test battery / audit script", "run against live sources", "record verdict + evidence leaf"],
        "research":    ["gather sources from memory/ pointer map", "compute/detect per protocol", "findings leaf + index line"],
        "measurement": ["instrument or extend scorer", "two-run delta check", "publish snapshot + report leaf"],
        "ops":         ["pre-flight checks (targets exist, idempotent)", "execute from non-sandbox session", "verify registration/health + evidence leaf"],
    }
    return base[gtype]


def _backlog_candidates():
    cands = []
    try:
        t = open(os.path.join(HERE, "scheduled-background.md"), encoding="utf-8").read()
        for m in re.finditer(r"^-\s*([A-Z]+)#(\d+):\s*(.+)$", t, re.M):
            cands.append({"agent": m.group(1).lower(), "ref": "%s#%s" % (m.group(1), m.group(2)),
                          "text": m.group(3).strip()[:200], "source": "scheduled-background.md"})
    except Exception:
        pass
    return cands


def _why(it, lane_note):
    parts = ["planned as %s work (cx%d)" % (it["type"], it["complexity"])]
    if it.get("source"):
        parts.append("from ranked backlog (%s) - already triaged in a prior cycle, so no new research cost" % it["ref"])
    else:
        parts.append("already open on the %s lane - FIFO order keeps evidence leaves consistent" % it["agent"])
    p = it.get("p_reached", 0.85)
    if p >= 0.9:
        parts.append("high confidence (P(reached) ~%.0f%%): type+complexity slip model sees low risk" % (100 * p))
    elif p >= 0.7:
        parts.append("moderate confidence (P(reached) ~%.0f%%): slip model flags some risk, ETA already inflated" % (100 * p))
    else:
        parts.append("lower confidence (P(reached) ~%.0f%%): kept in plan because its scope gates later work" % (100 * p))
    if lane_note:
        parts.append(lane_note)
    return "; ".join(parts)


def build_plan(doc):
    """Return {cycle_state, level_up_eta, planned: [items with why], horizons: [...], tree: {...}}."""
    fleet = doc.get("fleet", {})
    pct = fleet.get("pct", 0)
    done, total = fleet.get("done", 0), fleet.get("total", 0)
    gen = datetime.strptime(doc["generated"], "%Y-%m-%d %H:%M:%S") if doc.get("generated") else datetime.now()
    next10 = doc.get("next10") or []
    level_up_eta = doc.get("level_up_eta")
    all_clear = pct >= 99.95 and not next10

    planned, lane_t = [], {}
    if all_clear:
        # Project the NEXT cycle: ranked backlog candidates become goals at kickoff.
        for i, c in enumerate(_backlog_candidates()[:8]):
            gtype, cx = _classify(c["text"]), _complexity(c["text"])
            hours = BASE_HOURS[gtype] * COMPLEX_MULT[cx]
            lane_t[c["agent"]] = lane_t.get(c["agent"], gen) + timedelta(hours=hours)
            eta = lane_t[c["agent"]]
            planned.append({"rank": i + 1, "agent": c["agent"], "goal": c["text"], "title": c["text"][:80],
                            "type": gtype, "complexity": cx, "p_reached": 0.85,
                            "eta": eta.strftime("%Y-%m-%d %H:%M"), "hours": round(hours, 2),
                            "ref": c.get("ref"), "source": c.get("source"), "projected": True})
        cycle_state = "all-clear: level-up gated, next cycle projected from ranked backlog"
    else:
        for it in next10:
            planned.append(dict(it, projected=False))
        anchor = datetime.strptime(level_up_eta, "%Y-%m-%d %H:%M") if level_up_eta else gen
        cycle_state = "in flight: %d goal(s) open" % len(next10)

    # lane note per agent for the 'why'
    lanes = doc.get("lanes", {})
    for it in planned:
        lane = lanes.get(it["agent"], {})
        note = ("lane %s has %d/%d done; this goal ends its lane at %s" %
                (it["agent"], lane.get("done", 0), lane.get("total", 0), it["eta"])) if lane.get("end") else None
        it["why"] = _why(it, note)
        it["steps"] = it.get("steps") or _steps_for(it["type"])
        it["outcome"] = "reached ~%s (P~%.0f%%)" % (it["eta"], 100 * it["p_reached"])

    # decision-tree chaining: if this goal is reached, what starts next in its lane?
    by_agent = {}
    for it in planned:
        by_agent.setdefault(it["agent"], []).append(it)
    for items in by_agent.values():
        for j, it in enumerate(items):
            if j + 1 < len(items):
                nx = items[j + 1]
                it["then"] = "#%d [%s] %s" % (nx["rank"], nx["agent"], nx["title"][:70])
                it["then_eta"] = nx["eta"]
            else:
                it["then"] = "lane clear - level-up gate re-check (%s)" % (level_up_eta or "-")
                it["then_eta"] = level_up_eta

    horizons = []
    for label, hrs in HORIZONS:
        end = gen + timedelta(hours=hrs)
        completes = [it for it in planned if datetime.strptime(it["eta"], "%Y-%m-%d %H:%M") <= end]
        projected_new = sum(1 for it in completes if it.get("projected"))
        h = {"label": label, "hours": hrs, "end": end.strftime("%Y-%m-%d %H:%M"),
             "completes": len(completes), "top": [], "why_line": ""}
        for it in completes[:5]:
            h["top"].append({"rank": it["rank"], "agent": it["agent"], "title": it["title"][:90],
                             "eta": it["eta"], "type": it["type"], "why": it["why"]})
        if all_clear:
            if completes:
                h["why_line"] = ("cycle N+1 kicks off after the level-up gate; these are the first %d planned goal(s) "
                                 "to land by %s - expected outcome: fleet ~%.0f%% of the NEW cycle done") % (
                                 len(completes), h["end"], 100.0 * projected_new / max(1, min(8, len(planned))))
            else:
                h["why_line"] = ("no goal work planned yet - the fleet is all-clear; the only action in this window is the "
                                 "level-up gate + cycle proposal, so nothing completes by %s") % h["end"]
        else:
            h["why_line"] = ("queue order from the auto-loop: these complete first because their lanes are shortest; "
                             "expected outcome: fleet %d/%d -> %d%%") % (
                             done, total, min(100.0, 100.0 * (done + len(completes)) / max(1, total)))
        horizons.append(h)

    tree = {"state": "Fleet %d/%d (%.0f%%)" % (done, total, pct),
            "gate": "all goals 100%?", "branch_taken": "YES - all-clear" if all_clear else "NO - queue in flight",
            "yes": {"action": "level-up gate fires -> Lv increments, report written",
                    "then": "Orchestrator proposes cycle N+1 from ranked backlog (%d candidates)" % len(_backlog_candidates()[:8]),
                    "first_planned": ["#%d [%s] %s ~%s" % (it["rank"], it["agent"], it["title"][:60], it["eta"]) for it in planned[:4]]},
            "no": {"action": "keep current queue; next completion gates progress",
                   "then": "when the last lane ends (%s) the gate re-checks" % (level_up_eta or "-"),
                   "first_planned": ["#%d [%s] %s ~%s" % (it["rank"], it["agent"], it["title"][:60], it["eta"]) for it in planned[:4]]}}
    return {"cycle_state": cycle_state, "level_up_eta": level_up_eta, "planned": planned,
            "horizons": horizons, "tree": tree}


def load_plan():
    doc = json.load(open(os.path.join(HERE, "next10.json"), encoding="utf-8"))
    return doc, build_plan(doc)
