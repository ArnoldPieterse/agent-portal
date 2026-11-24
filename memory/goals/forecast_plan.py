#!/usr/bin/env python3
"""Planned-work layer over next10.json (2026-11-24, Orchestrator seat).

next10.json says HOW the forecast works; this module answers WHAT is planned:
  - per horizon: which goals are planned to complete, expected outcome, and WHY each
  - when the fleet is all-clear (next10 empty): projects the NEXT cycle from the
    ranked backlog candidates, so every horizon always carries concrete planned work
  - a decision tree: state -> gate (all goals 100%?) -> level-up + new cycle | keep queue

Stdlib only. Used by make_forecast_deck.py and forecast_engine._write_outputs.
"""
import hashlib
import json
import math
import os
import re
import sys
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


# ---- Functional deliverables layer (PM view) ---------------------------------
# Maps goal text -> the functional capability it delivers, so the forecast can
# speak in deliverables ("camera access") instead of raw task titles.
CAPABILITY_MAP = [
    (r"custom input|input detection", "Custom input detection", "Input & accessibility"),
    (r"keyboard nav|aria", "Keyboard navigation", "Input & accessibility"),
    (r"camera|screen capture", "Camera access", "Peripherals"),
    (r"\bmics?\b|microphone|\bvoice\b", "Mic access", "Peripherals"),
    (r"mode transition|fleet mode", "Fleet mode switching", "Portal UX"),
    (r"idle task|idle-task|injector", "Idle-task injection", "Automation"),
    (r"load test|probe", "Load-test evidence", "Reliability"),
    (r"mirror.*drift|drift.*mirror", "Mirror self-healing", "Reliability"),
    (r"chaos drill", "Chaos-drill runbook", "Reliability"),
    (r"schtasks?|dependency graph", "Scheduled-task graph", "Ops automation"),
    (r"decay model|knowledge decay", "Knowledge-decay scoring", "Memory quality"),
    (r"compression fidelity|self-audit", "Synthesis self-audit", "Memory quality"),
    (r"forecast|prediction|calibrat", "Forecast calibration", "Planning"),
    (r"productivity baseline|productivity trend", "Productivity baseline", "Measurement"),
    (r"merge queue|merge-integration", "Merge-queue integration", "Ops automation"),
    (r"archive", "Archive + evidence leaves", "Memory quality"),
]

# The PM's functional chain: each step, once landed, unblocks the next.
CAPABILITY_LADDER = [
    ("Keyboard navigation", "Full keyboard control of the portal - no mouse needed to run the fleet."),
    ("Camera access", "Vision into any screen/app - reading tenders, posts and dashboards."),
    ("Mic access", "Hearing + speaking - phone calls and voice interaction become possible."),
    ("Custom input detection", "Arbitrary device/input sensing - full autonomous action stack."),
]

# 30-day business outcomes (PM view) - OUTCOME CATALOG (data, not schedule).
# Each row declares WHAT an outcome is and what GATES it (capability names or other
# outcome names), plus ramp/run days. The actual day windows are COMPUTED on every
# refresh from live state: reached capabilities = day 0, in-plan capabilities = their
# ETA day, unqueued ones projected via fleet throughput. As goals are reached the
# plan re-derives itself continuously (history kept in forecast/plans-history.jsonl).
# tuple: (name, gates, ramp_days, run_days, lane_hint)
OUTCOME_CATALOG = [
    ("Generate daily social media posts", ["Custom input detection"], 1, 2, None),
    ("Commenting on posts",               ["Custom input detection"], 0, 4, None),
    ("Making phone calls",                ["Mic access"],             2, 7, None),
    ("Writing valid tenders",             ["Camera access"],          3, 10, None),
    ("Predicting markets",                [],                          5, 15, "researcher"),
    ("Making money (revenue channels live)", ["Custom input detection", "Camera access"], 3, 8, None),
    ("Positive money income (net > 0)",   ["Making money (revenue channels live)"], 7, 7, None),
]
OUTCOME_NOTES = {
    "Generate daily social media posts": "autonomous posting loop running unattended",
    "Commenting on posts": "reads threads and replies in-voice",
    "Making phone calls": "full-duplex voice calls, not just text",
    "Writing valid tenders": "reads tender PDFs/screens and drafts compliant responses",
    "Predicting markets": "model work on existing compute; gated by fleet throughput, not peripherals",
    "Making money (revenue channels live)": "at least one channel transacting autonomously",
    "Positive money income (net > 0)": "all revenue channels running >= 1 week with net positive",
}
OUTCOME_GATES = {name: gates for name, gates, _r, _d, _l in OUTCOME_CATALOG}
CAP_EST_HOURS = 6.0   # projected effort of one unqueued capability (build, cx2)
PLAN_HIST = os.path.join(HERE, "forecast", "plans-history.jsonl")


def _ledger():
    """Live goal ledger per agent: [{text, status, ...}] - single source of truth."""
    try:
        rd = os.path.join(os.path.dirname(HERE), "researcher")
        if rd not in sys.path:
            sys.path.insert(0, rd)
        import goal_ledger as gl
        gl.GOALS_DIR = HERE
        led = gl.build_ledger()
        out = {}
        for name, a in (led.get("agents") or {}).items():
            goals = a if isinstance(a, list) else a.get("goals", [])
            out[name] = [g for g in goals if isinstance(g, dict)]
        return out
    except Exception:
        return {}


def _capability_inventory(planned, ledger_agents):
    """Live capability status: done (reached goal matches) / in-plan (next-10 ETA) /
    queued (open goal outside next-10) / not-planned (no goal anywhere yet)."""
    inv = {}
    for pat, name, stream in CAPABILITY_MAP:
        rx = re.compile(pat)
        entry = {"name": name, "stream": stream, "status": "not-planned", "via": None,
                 "eta": None, "agent": None, "p_reached": None}
        for agent, goals in (ledger_agents or {}).items():
            if entry["status"] == "done":
                break
            for g in goals:
                if not rx.search(g.get("text", "")):
                    continue
                if g.get("status") == "reached":
                    entry.update(status="done", via="%s (reached goal)" % agent)
                    break
                if entry["status"] != "queued":
                    entry.update(status="queued", via="%s (open, outside next-10)" % agent)
        for it in planned:
            d = it.get("deliverable") or {}
            if d.get("name") == name and it.get("eta") and entry["status"] != "done":
                entry.update(status="in-plan",
                             via="#%d [%s] %s" % (it["rank"], it.get("agent", "?"), (it.get("title") or "")[:48]),
                             eta=it.get("eta"), agent=it.get("agent"), p_reached=it.get("p_reached"))
        inv[name] = entry
    return inv


def _schedule_outcomes(inv, gen, free_day):
    """Compute the 30-day plan: every window is derived from gate completion days,
    never hardcoded. start = max(gate days) + ramp; end = start + run.
    free_day = when the earliest lane frees a seat (unqueued work can only be
    scheduled once a seat is free, plus its work time)."""
    done_map, out = {}, []
    for name, gates, ramp, run, lane_hint in OUTCOME_CATALOG:
        gate_days, gate_desc, projected = [], [], []
        for gname in gates:
            if gname in done_map:  # gated by another planned outcome
                s = done_map[gname]
                gd, desc = s["end_day"], "%s (ends day %d)" % (gname, s["end_day"])
            else:
                e = inv.get(gname)
                if e and e["status"] == "done":
                    gd, desc = 0, "%s (already reached)" % gname
                elif e and e.get("eta"):
                    gd = max(1, int(math.ceil((datetime.strptime(e["eta"], "%Y-%m-%d %H:%M") - gen).total_seconds() / 86400.0)))
                    desc = "%s (planned ~day %d)" % (gname, gd)
                else:
                    gd = free_day + int(math.ceil(CAP_EST_HOURS / 24.0))
                    desc = "%s (not in queue - schedulable ~day %d: seat frees + work time)" % (gname, gd)
                    projected.append(gname)
            gate_days.append(gd)
            gate_desc.append(desc)
        start_day = max(gate_days, default=0) + ramp
        end_day = start_day + run
        status = "planned" if end_day <= 30 else ("at-risk (runs past day 30)" if start_day <= 30 else "beyond 30 days")
        lane = lane_hint or "fleet"
        for gname in reversed(gates):
            e = inv.get(gname)
            if e and e.get("agent"):
                lane = e["agent"]
                break
        o = {"name": name, "window": "day %d-%d" % (max(1, start_day), end_day),
             "start_day": max(1, start_day), "end_day": end_day, "status": status,
             "lane": lane, "gates": gate_desc, "via": "; ".join(gate_desc) or "foundation only",
             "note": OUTCOME_NOTES.get(name, ""), "projected_gates": projected}
        done_map[name] = o
        out.append(o)

    def depth(n, seen=()):  # transitively-gated count -> the cycle-closing outcome
        g = [x for x in OUTCOME_GATES[n] if x in done_map and x not in seen]
        return 1 + max((depth(x, seen + (n,)) for x in g), default=0)

    closing = max(out, key=lambda o: (depth(o["name"]), o["end_day"]))
    closing["cycle_closing"] = True
    return out


def _plan_history(outcomes, gen, fleet_pct):
    """Record the plan whenever it changes; return (sig, delta-vs-previous, recent)."""
    sig_src = json.dumps([[o["name"], o["start_day"], o["end_day"], o["status"]] for o in outcomes])
    sig = hashlib.sha1(sig_src.encode("utf-8")).hexdigest()[:12]
    entries = []
    try:
        with open(PLAN_HIST, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    delta = []
    if entries and entries[-1].get("sig") == sig:
        changed = False  # identical to what is already recorded - no new snapshot
    else:
        changed = True
        prev = (entries[-1] if entries else None)
        if prev:
            pmap = {o["name"]: o for o in prev.get("outcomes", [])}
            cur_names = {o["name"] for o in outcomes}
            for o in outcomes:
                p = pmap.get(o["name"])
                if not p:
                    delta.append("%s: new in plan (day %d-%d)" % (o["name"], o["start_day"], o["end_day"]))
                elif (p.get("start_day"), p.get("end_day"), p.get("status")) != (o["start_day"], o["end_day"], o["status"]):
                    delta.append("%s: day %s-%s -> day %d-%d (%s)" % (
                        o["name"], p.get("start_day", "?"), p.get("end_day", "?"),
                        o["start_day"], o["end_day"], o["status"]))
            for n in pmap:
                if n not in cur_names:
                    delta.append("%s: dropped from plan" % n)
        else:
            delta.append("first computed 30-day plan")
        entry = {"ts": gen.strftime("%Y-%m-%d %H:%M:%S"), "sig": sig, "fleet_pct": fleet_pct,
                 "outcomes": [{"name": o["name"], "start_day": o["start_day"],
                               "end_day": o["end_day"], "status": o["status"]} for o in outcomes]}
        entries.append(entry)
        try:
            os.makedirs(os.path.dirname(PLAN_HIST), exist_ok=True)
            with open(PLAN_HIST, "w", encoding="utf-8") as f:
                for e in entries[-150:]:
                    f.write(json.dumps(e) + "\n")
        except Exception:
            pass
    recent = [{"ts": e["ts"], "sig": e["sig"]} for e in entries[-5:]]
    return sig, delta, recent


def _deliverable(title, goal):
    text = "%s %s" % (title or "", goal or "")
    for pat, name, stream in CAPABILITY_MAP:
        if re.search(pat, text, re.I):
            return {"name": name, "stream": stream}
    short = (title or "").strip()
    return {"name": short[:60], "stream": "General"}


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


def _cap_done_day(e, gen):
    """Completion day (from now) for one capability inventory entry; 0 = done."""
    if not e or e.get("status") == "done":
        return 0
    m = re.search(r"~day (\d+)", e.get("desc") or "")
    if m:
        return max(0, int(m.group(1)))
    eta = e.get("eta")
    if eta:
        try:
            return max(0, int((datetime.strptime(eta, "%Y-%m-%d %H:%M") - gen).total_seconds() // 86400))
        except Exception:
            pass
    return None


def _derive_15d(outcomes, inv, gen):
    """Derive the 15-day plan FROM the 30-day one: same outcomes clamped to days
    0-15 and split into concrete steps (gates -> setup -> first delivery ->
    stabilize). An outcome landing after day 15 appears as a 'prep' entry - the
    gate work that must finish inside the window for the 30-day plan to hold.
    Re-derived on every refresh from the same live inputs as the 30-day plan."""
    H = 15
    ramp_run = {n: (r, d) for n, _g, r, d, _l in OUTCOME_CATALOG}
    end_by_name = {o2["name"]: o2.get("end_day") for o2 in outcomes}
    out = []
    for o in outcomes:
        m = re.search(r"day (\d+)-(\d+)", o.get("window") or "")
        cc = bool(o.get("cycle_closing"))
        if not m:  # already done, or no window yet
            done = o.get("status") == "done"
            out.append({"name": o["name"], "parent": None,
                        "window": "done" if done else "beyond 15d",
                        "status": o.get("status", "?"), "cycle_closing": cc,
                        "steps": ([{"days": "-", "text": "already reached - nothing to do in this window"}]
                                  if done else [])})
            continue
        S, E = int(m.group(1)), int(m.group(2))
        gnames = OUTCOME_GATES.get(o["name"], [])
        gdescs = o.get("gates") or []
        gi = []
        for i, g in enumerate(gnames):
            e = inv.get(g)
            desc = gdescs[i] if i < len(gdescs) else None
            if e:  # capability gate - live inventory status
                gi.append((g, _cap_done_day(e, gen), e.get("status"), desc))
            else:  # gate is another planned outcome - use its computed end day
                gi.append((g, end_by_name.get(g), "planned outcome", desc))
        mg = max([d for _g, d, _s, _v in gi if d is not None] or [0])
        ramp, run = ramp_run.get(o["name"], (1, 3))
        if S > H:  # lands later -> show the prep that must finish by day 15
            st = []
            for g, d, s, v in gi:
                if s == "done":
                    continue
                when = ("by ~day %d" % min(d, H)) if d is not None else "before day %d" % H
                st.append({"days": "day 0-%d" % min(max(d or H, 1), H),
                           "text": "%s must be done %s" % ((v or g), when)})
            if not st:
                st.append({"days": "day 0-%d" % H, "text": "no gate work left - execution only (starts day %d)" % S})
            out.append({"name": o["name"] + " - prep", "parent": o["name"], "window": "day 1-%d" % H,
                        "status": "prep for day %d start" % S, "cycle_closing": cc, "steps": st})
        else:
            st = []
            og = [(g, d, s, v) for g, d, s, v in gi if s != "done"]
            if og:
                st.append({"days": "day 0-%d" % min(mg, S), "text": "gates clear: " + "; ".join(
                    (v if s == "planned outcome" else
                     "%s by ~day %d%s" % (g, (d if d is not None else S), (" (%s)" % s) if s != "in-plan" else ""))
                    for g, d, s, v in og)})
            e15 = min(E, H)
            se = min(S + max(ramp - 1, 0), e15)
            if se >= S:
                st.append({"days": "day %d-%d" % (S, se), "text": "setup + first runs of " + o["name"]})
            mid = min(S + ramp, E)
            if mid <= e15 and mid > se:
                st.append({"days": "day %d" % mid, "text": "first real delivery (usable output)"})
            if E > H:
                st.append({"days": "day %d-%d" % (max(mid, S), H),
                           "text": "stabilize - daily runs; continues to day %d of the 30-day plan" % E})
            elif len(st) < 3:
                st.append({"days": "day %d-%d" % (max(se + 1, S), e15),
                           "text": "stabilize - daily runs through day %d" % e15})
            out.append({"name": o["name"], "parent": None, "window": "day %d-%d" % (S, e15),
                        "status": ("lands fully inside 15d" if E <= H
                                   else "starts day %d, runs to day %d of the 30-day plan" % (S, E)),
                        "cycle_closing": cc, "steps": st})
    return out


def _day_spec(s):
    """Parse 'day X' or 'day X-Y' -> (x, y); None when no day is stated."""
    m = re.search(r"day (\d+)(?:-(\d+))?", s or "")
    if not m:
        return None
    a = int(m.group(1))
    b = int(m.group(2) or m.group(1))
    return a, b


def _clamp_window(win, H):
    """Clamp a 'day X-Y' window to the [0,H] horizon; note when it runs on."""
    spec = _day_spec(win)
    if spec is None:
        return win
    a, b = spec
    if a > H:
        return "day %d+ (see 15-day plan)" % a
    nb = min(H, b)
    cont = " -> runs to day %d" % b if b > H else ""
    return "day %d-%d%s" % (a, nb, cont)


def _expand_step(text, a, b, H):
    """Break one 15-day step (clamped to [a,b], both <=H) into finer sub-steps.
    This is the extra detail the 7-day plan adds over the 15-day one: gate steps
    are split into one line per gate pinned to its own ETA day, and setup/stabilize
    windows are split into scaffold -> first run -> verify / monitor."""
    t = text.lower()
    subs = []
    if "gates clear" in t:
        body = text.split(":", 1)[1] if ":" in text else text
        parts = [p.strip() for p in body.split(";") if p.strip()]
        if parts:
            for part in parts:
                m = re.search(r"~day (\d+)", part)
                d = int(m.group(1)) if m else a
                flag = " (after the 7-day window)" if d > H else ""
                subs.append(("day %d" % d, "%s%s" % (part, flag)))
        else:
            subs.append(("day %d-%d" % (a, b), text))
    elif "setup" in t:
        name = text.split(" of ", 1)[1] if " of " in text else ""
        span = b - a + 1
        if span <= 1:
            subs.append(("day %d" % a, "scaffold + wire up %s; first automated run" % name))
        else:
            mid = (a + b) // 2
            subs.append(("day %d" % a, "scaffold + wire up %s" % name))
            if mid > a:
                subs.append(("day %d" % mid, "first automated run of %s" % name))
            subs.append(("day %d" % b, "fix issues; verify first output of %s" % name))
    elif "first real delivery" in t:
        subs.append(("day %d" % a, "produce first usable output + record evidence leaf"))
    elif "stabilize" in t or "daily runs" in t:
        if b - a + 1 <= 1:
            subs.append(("day %d" % a, text))
        else:
            subs.append(("day %d" % a, "daily unattended runs begin"))
            subs.append(("day %d" % b, "monitor + regression check on the loop"))
    else:
        subs.append(("day %d-%d" % (a, b), text))
    return subs


def _derive_7d(o15):
    """Derive the 7-day plan FROM the 15-day one: every 15-day step is clamped to
    days 0-7 and expanded into finer sub-steps (per-gate lines, scaffold -> run ->
    verify). A step running past day 7 is cut at the edge and marked as continuing
    in the 15-day plan; a step starting after day 7 appears as a 'watch' note.
    Purely derived from o15, so it re-derives on every refresh with the rest."""
    H = 7
    out = []
    for e in o15:
        steps7 = []
        for s in e.get("steps") or []:
            spec = _day_spec(s["days"])
            if spec is None:  # e.g. 'already reached - nothing to do'
                steps7.append({"days": s["days"], "text": s["text"]})
                continue
            a, b = spec
            if a > H:  # starts after the 7-day window -> watch note
                steps7.append({"days": "day %d" % a,
                               "text": "%s (after the 7-day window - see 15-day plan)" % s["text"]})
                continue
            na, nb = max(0, a), min(H, b)
            cont = " - continues in the 15-day plan to day %d" % b if b > H else ""
            subs = _expand_step(s["text"], na, nb, H)
            for i, (dspec, txt) in enumerate(subs):
                steps7.append({"days": dspec, "text": txt + (cont if i == len(subs) - 1 else "")})
        out.append({"name": e["name"], "parent": e.get("parent"),
                    "window": _clamp_window(e.get("window"), H),
                    "status": e.get("status", ""), "cycle_closing": bool(e.get("cycle_closing")),
                    "steps": steps7})
    return out


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
        it["deliverable"] = _deliverable(it.get("title"), it.get("goal"))

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
    # ---- capability chain + 30-day outcomes (PM view) ------------------------
    # All computed from live state on every refresh: the ledger says which
    # capabilities are already reached, next-10 ETAs say which land when, and fleet
    # throughput projects what is not queued yet. As goals are reached, windows
    # shift - the plan re-derives itself continuously (see plans-history.jsonl).
    tpgh = float(doc.get("throughput_goals_per_hour") or 0.3)
    inv = _capability_inventory(planned, _ledger())
    ladder_names = [c[0] for c in CAPABILITY_LADDER]
    chain = []
    for i, (name, note) in enumerate(CAPABILITY_LADDER):
        nxt = ladder_names[i + 1] if i + 1 < len(ladder_names) else "30-day business outcomes"
        e = inv.get(name) or {"status": "not-planned", "via": None, "eta": None, "p_reached": None}
        chain.append({"step": i + 1, "name": name, "note": note, "status": e["status"],
                      "via": e.get("via"), "eta": e.get("eta"), "p_reached": e.get("p_reached"),
                      "unlocks": nxt})

    free_day = 0
    ends = [l.get("end") for l in (doc.get("lanes") or {}).values() if l.get("end")]
    if ends:
        first_free = min(datetime.strptime(e, "%Y-%m-%d %H:%M") for e in ends)
        free_day = max(0, int(math.ceil((first_free - gen).total_seconds() / 86400.0)))
    outcomes = _schedule_outcomes(inv, gen, free_day)
    outcomes_15d = _derive_15d(outcomes, inv, gen)
    outcomes_7d = _derive_7d(outcomes_15d)
    sig, delta, recent = _plan_history(outcomes, gen, pct)
    plan_meta = {"sig": sig,
                 "computed_at": gen.strftime("%Y-%m-%d %H:%M:%S"),
                 "basis": "live goal ledger + next-10 ETAs + fleet throughput ~%.2f goals/h; recomputed every refresh" % tpgh,
                 "delta": delta, "history": recent}

    return {"cycle_state": cycle_state, "level_up_eta": level_up_eta, "planned": planned,
            "horizons": horizons, "tree": tree,
            "capability_chain": chain, "outcomes_30d": outcomes,
            "outcomes_15d": outcomes_15d, "outcomes_7d": outcomes_7d, "plan_meta": plan_meta}


def load_plan():
    doc = json.load(open(os.path.join(HERE, "next10.json"), encoding="utf-8"))
    return doc, build_plan(doc)
