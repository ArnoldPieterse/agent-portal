#!/usr/bin/env python3
"""Fleet Forecast Engine - 10 steps ahead (2026-11-23, Orchestrator seat).

Predicts the next 10 goals/steps the fleet will attempt and projects outcomes at five
horizons: 30 minutes, 1 hour, 1 day, 1 week, 1 month. Deterministic (stdlib only -
runs under pythonw schtask, no LLM): goal ETAs come from per-type base hours x complexity,
slip inflation from the v2 naive-Bayes slip model (memory/goals/slip_prediction_table.json),
and queue order mirrors the auto-loop (per-agent FIFO lanes, parallel seats).

Outputs (memory/goals/ - alongside the goal files, like the existing forecast-*.md leaves):
  next10.json        machine-readable next-10 queue + horizon summary (portal reads this)
  forecast-latest.md human-readable 5-horizon cards (agents read this)
  history/*.json     rotated snapshots (keep 48) for calibration
  calibration.json   rolling prediction-vs-actuals scores per horizon
  cycle-proposal.md  ranked candidate goals for the NEXT cycle (alignment hook)

Alignment: /api/goals/forecast serves next10.json; build_system_prompt injects a compact
per-agent forecast block so goal FOLLOWING tracks the prediction, and cycle-proposal.md
gives the Orchestrator pre-computed candidates when a cycle completes.

Usage:
  python memory/goals/forecast_engine.py [--refresh] [--json] [--quiet]
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta

_HD = os.path.dirname(os.path.abspath(__file__))          # sibling module must resolve when loaded in-process by the portal
if _HD not in sys.path:
    sys.path.insert(0, _HD)
try:
    from forecast_plan import build_plan  # planned-work layer (same dir)
except Exception:  # engine must never die because the plan layer is missing
    build_plan = None

HERE = os.path.dirname(os.path.abspath(__file__))          # memory/goals
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))     # project root
OUT = HERE                                                 # forecasts live next to goals
HIST = os.path.join(OUT, "history")
HORIZONS = [
    ("30m",  0.5),
    ("1h",   1.0),
    ("1d",   24.0),
    ("1w",   168.0),
    ("1m",   720.0),
]
TYPE_PAT = [
    ("verify",      re.compile(r"(?i)\b(verify|validation|benchmark|regression test|audit|consistency check|compliance)\b")),
    ("research",    re.compile(r"(?i)\b(research|detector|matcher|anomaly|conflict|pattern|precedent|analysis)\b")),
    ("measurement", re.compile(r"(?i)\b(measure|monitor|heatmap|scoring|track|score|histogram|benchmark suite)\b")),
    ("ops",         re.compile(r"(?i)\b(schtask|deploy|runbook|maintenance window|recovery|heal|lifecycle|arbitration)\b")),
]
BASE_HOURS = {"build": 4.0, "verify": 2.0, "research": 5.0, "measurement": 3.0, "ops": 2.0}
COMPLEX_MULT = {1: 1.0, 2: 1.6, 3: 2.5}


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _open_goals():
    """Per-agent open goal lists via the evidence-gated ledger (single source of truth)."""
    sys.path.insert(0, os.path.join(ROOT, "memory", "researcher"))
    try:
        import goal_ledger as gl
        gl.GOALS_DIR = HERE
        led = gl.build_ledger()
    except Exception as e:
        return {}, {"error": str(e)}
    out, meta = {}, {}
    for name, a in (led.get("agents") or {}).items():
        goals = a if isinstance(a, list) else a.get("goals", [])
        open_g = [g["text"] for g in goals if g.get("status") != "reached"]
        out[name] = {
            "open": open_g,
            "done": sum(1 for g in goals if g.get("status") == "reached"),
            "total": len(goals),
        }
    meta.update({"fleet_done": led.get("fleet_reached", 0),
                 "fleet_total": led.get("fleet_total_goals", 0)})
    return out, meta


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


def _slip_prob(table, gtype, agent, complexity):
    """Naive-Bayes P(slip) from the v2 table; degrades to the training slip rate."""
    if not table:
        return 0.25
    try:
        p = float(table.get("slip_rate_training", 0.25))
        cp = table.get("conditional_log_probs", {})
        lp_s, lp_n = None, None
        v = cp.get("type|%s" % gtype)
        if v and len(v) >= 2:
            lp_s, lp_n = float(v[0]), float(v[1])
        a = cp.get("agent|%s" % agent.lower())
        if a and len(a) >= 2:
            lp_s = (lp_s or -1.5) + float(a[0]) - float(a[1])
            lp_n = (lp_n or -1.5) + float(a[1]) - float(a[1])  # agent fold already in slip term
        c = cp.get("complexity|%d" % complexity)
        if c and len(c) >= 2:
            lp_s = (lp_s or -1.5) + float(c[0])
            lp_n = (lp_n or -1.5) + float(c[1])
        if lp_s is None or lp_n is None:
            return p
        import math
        z = lp_s - lp_n
        return 1.0 / (1.0 + math.exp(-z))
    except Exception:
        return 0.25


def _steps_for(gtype, text):
    tail = ""
    m = re.search(r"(?i)verified\s*:\s*(.+)$", text)
    if m:
        tail = "evidence leaf + index line (AC: %s)" % m.group(1).strip()[:90]
    base = {
        "build":       ["scaffold the module file", "implement core logic", "self-test until AC green", tail or "write evidence leaf + index line"],
        "verify":      ["build the test battery / audit script", "run against live sources", "record verdict + evidence leaf"],
        "research":    ["gather sources from memory/ (pointer map)", "compute/detect per protocol", "write findings leaf + index line"],
        "measurement": ["instrument or extend the scorer", "two-run delta check", "publish snapshot + report leaf"],
        "ops":         ["pre-flight checks (targets exist, idempotent)", "execute from non-sandbox session", "verify registration/health + evidence leaf"],
    }[gtype]
    return [s for s in base if s]


def _throughput():
    """Goals closed per active hour, from cycle history (levels.json + retro files)."""
    rate = 6.0  # fallback: ~80 goals / ~2.5 working days observed across cycles
    try:
        lv = _load_json(os.path.join(ROOT, "memory", "levels.json")) or {}
        hist = lv.get("history") or []
        if len(hist) >= 2:
            d0 = datetime.strptime(hist[0]["ts"], "%Y-%m-%d %H:%M:%S")
            d1 = datetime.strptime(hist[-1]["ts"], "%Y-%m-%d %H:%M:%S")
            hrs = max(1.0, (d1 - d0).total_seconds() / 3600.0)
            rate = max(2.0, min(30.0, (hist[-1]["level"] * 80.0) / hrs))
    except Exception:
        pass
    return rate


def _backlog_candidates():
    """Ranked next-cycle candidates: scheduled-background backlog + successor patterns."""
    cands = []
    try:
        t = open(os.path.join(HERE, "scheduled-background.md"), encoding="utf-8").read()
        for m in re.finditer(r"^-\s*([A-Z]+)#(\d+):\s*(.+)$", t, re.M):
            cands.append({"agent": m.group(1).lower(), "ref": "%s#%s" % (m.group(1), m.group(2)),
                          "text": m.group(3).strip()[:160], "source": "scheduled-background"})
    except Exception:
        pass
    return cands[:12]


def refresh(now=None):
    now = now or datetime.now()
    lanes, meta = _open_goals()
    table = _load_json(os.path.join(HERE, "slip_prediction_table.json"))
    rate = _throughput()
    fleet_done, fleet_total = meta.get("fleet_done", 0), meta.get("fleet_total", 0)

    # Per-agent FIFO lanes with cumulative ETAs (seats run in parallel).
    items, lane_end = [], {}
    for agent, st in sorted(lanes.items()):
        t = now
        for i, text in enumerate(st["open"]):
            gtype = _classify(text)
            cx = _complexity(text)
            p_slip = _slip_prob(table, gtype, agent, cx)
            hours = BASE_HOURS[gtype] * COMPLEX_MULT[cx]
            hours *= 1.0 / (1.0 + 0.5 * p_slip)          # slip-prone goals take longer
            t = t + timedelta(hours=hours)
            items.append({"agent": agent, "goal": text[:220], "type": gtype, "complexity": cx,
                          "p_reached": round(1.0 - p_slip, 3), "eta": t.strftime("%Y-%m-%d %H:%M"),
                          "hours": round(hours, 2), "order": i})
        lane_end[agent] = t
    items.sort(key=lambda x: (x["eta"], x["agent"], x["order"]))
    for r, it in enumerate(items, 1):
        it["rank"] = r
        m = re.match(r"\*\*(.+?)\*\*", it["goal"])
        it["title"] = (m.group(1).strip() if m else it["goal"][:80])
    next10 = items[:10]

    # Consequences: keyword overlap with other open goals + level-up timing.
    kw = {}
    for it in items:
        toks = set(re.findall(r"[a-z]{5,}", it["goal"].lower())) - {
            "python", "memory", "evidence", "index", "verified", "goal", "agent", "fleet"}
        kw[it["rank"]] = toks
    for it in next10:
        rel = []
        for other in items:
            if other is it or len(rel) >= 3:
                continue
            ov = kw[it["rank"]] & kw.get(other["rank"], set())
            if len(ov) >= 2:
                rel.append("%s: %s (%s) - shared scope %s" % (other["agent"], other["goal"][:60], other["eta"], ",".join(sorted(ov)[:3])))
        cons = list(rel)
        if lane_end:
            slowest = max(lane_end, key=lane_end.get)
            cons.append("lane end %s: %s (slowest lane)" % (slowest, lane_end[slowest].strftime("%m-%d %H:%M")))
        it["steps"] = _steps_for(it["type"], it["goal"])
        it["outcome"] = ("reached ~%s (P=%.0f%%)" % (it["eta"], 100 * it["p_reached"]))
        it["consequences"] = cons

    # Horizon projections.
    horizons = []
    for label, hrs in HORIZONS:
        end = now + timedelta(hours=hrs)
        completes = [it for it in items if datetime.strptime(it["eta"], "%Y-%m-%d %H:%M") <= end]
        pct = round(100.0 * (fleet_done + len(completes)) / fleet_total, 1) if fleet_total else 0
        h = {"label": label, "hours": hrs, "end": end.strftime("%Y-%m-%d %H:%M"),
             "completes": len(completes), "fleet_pct": pct,
             "top": ["#%d %s: %s (%s)" % (it["rank"], it["agent"], it["title"][:70], it["eta"]) for it in completes[:5]]}
        if label in ("1w", "1m"):
            h["next_cycle_candidates"] = _backlog_candidates()[:8]
        horizons.append(h)

    doc = {"ok": True, "generated": now.strftime("%Y-%m-%d %H:%M:%S"),
           "fleet": {"done": fleet_done, "total": fleet_total,
                     "pct": round(100.0 * fleet_done / fleet_total, 1) if fleet_total else 0},
           "throughput_goals_per_hour": round(rate, 2),
           "next10": next10, "horizons": horizons,
           "lanes": {a: {"done": s["done"], "total": s["total"],
                          "end": (lane_end[a].strftime("%Y-%m-%d %H:%M") if a in lane_end else None)}
                     for a, s in sorted(lanes.items())}}
    # Fleet all-clear ETA = the last lane to finish; this is when a fresh 100% can gate a level-up.
    doc["level_up_eta"] = max((v["end"] for v in doc["lanes"].values() if v["end"]), default=None)
    if build_plan is not None:
        try:
            doc["plan"] = build_plan(doc)  # WHAT is planned (deck + portal read this)
        except Exception:
            pass
    _write_outputs(doc)
    return doc


def _write_outputs(doc):
    os.makedirs(HIST, exist_ok=True)
    with open(os.path.join(OUT, "next10.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
    # Human cards
    L = ["# Fleet Forecast - 10 steps ahead", "", "Generated: %s | Fleet: %d/%d (%.0f%%) | throughput ~%.1f goals/h"
         % (doc["generated"], doc["fleet"]["done"], doc["fleet"]["total"], doc["fleet"]["pct"], doc["throughput_goals_per_hour"]), ""]
    L += ["## Next 10 goals (queue order)", ""]
    for it in doc["next10"]:
        L.append("**#%d [%s] %s** - ETA %s, P(reached) %.0f%% (%s, cx%d)"
                 % (it["rank"], it["agent"], it["title"], it["eta"], 100 * it["p_reached"], it["type"], it["complexity"]))
        L.append("   steps: " + " -> ".join(it["steps"]))
        if it["consequences"]:
            L.append("   consequences: " + " | ".join(it["consequences"][:3]))
    plan = doc.get("plan")
    if plan:
        L += ["", "## Planned work (decision tree)", "",
              "- state: %s | gate: %s -> **%s**" % (plan["tree"]["state"], plan["tree"]["gate"], plan["tree"]["branch_taken"]),
              "- cycle: %s" % plan["cycle_state"]]
        for it in plan["planned"][:8]:
            d = (it.get("deliverable") or {}).get("name", "")
            L.append("- #%d [%s] %s ~%s (P~%.0f%%) - %s%s" % (
                it["rank"], it["agent"], it["title"], it["eta"], 100 * it["p_reached"],
                it["why"][:140], (" | delivers: " + d) if d else ""))
        cc = plan.get("capability_chain")
        if cc:
            L += ["", "## Functional capability chain (PM view)", "",
                  "If each step lands it unblocks the next - this is how the fleet earns its 30-day deliverables:  "]
            for c in cc:
                line = "%d. **%s** [%s]" % (c["step"], c["name"], c["status"])
                if c.get("via"):
                    line += " - via %s ~%s" % (c["via"], (c.get("eta") or "-")[:16])
                L.append(line + "  -> unlocks: " + c["unlocks"])
        oc = plan.get("outcomes_30d")
        if oc:
            L += ["", "## 30-day business outcomes (PM view)", ""]
            for o in oc:
                line = "- **%s** - window %s | %s" % (o["name"], o["window"], o["status"])
                if o.get("via"):
                    line += " (gated by " + o["via"] + ")"
                L.append(line)
    for h in doc["horizons"]:
        L += ["", "## %s ahead (by %s)" % (h["label"], h["end"]),
              "- completes: **%d** goal(s) -> fleet ~%.0f%%" % (h["completes"], h["fleet_pct"])]
        for t in h["top"]:
            L.append("  - " + t)
        if plan and plan["horizons"]:
            ph = plan["horizons"][doc["horizons"].index(h)]
            if ph.get("why_line"):
                L.append("- why: " + ph["why_line"])
        if h.get("next_cycle_candidates"):
            L.append("- next-cycle candidates: " + "; ".join(c["ref"] + " " + c["text"][:50] for c in h["next_cycle_candidates"][:4]))
    with open(os.path.join(OUT, "forecast-latest.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    # Rotated history (keep 48)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    with open(os.path.join(HIST, "forecast-%s.json" % ts), "w", encoding="utf-8") as f:
        json.dump(doc, f)
    try:
        olds = sorted(os.listdir(HIST))
        for o in olds[:-48]:
            os.remove(os.path.join(HIST, o))
    except Exception:
        pass
    _calibrate(doc)
    _cycle_proposal(doc)


def _calibrate(doc):
    """Score the PREVIOUS next10 against current reality; keep rolling stats."""
    cal = _load_json(os.path.join(OUT, "calibration.json")) or {"runs": [], "rolling": {}}
    prev = None
    try:
        olds = sorted(f for f in os.listdir(HIST) if f.startswith("forecast-"))
        # the snapshot written just now is newest; previous = second-newest
        if len(olds) >= 2:
            prev = _load_json(os.path.join(HIST, olds[-2]))
    except Exception:
        pass
    if not prev or not prev.get("next10"):
        cal["last_check"] = doc["generated"] + " (no prior forecast to score)"
        with open(os.path.join(OUT, "calibration.json"), "w", encoding="utf-8") as f:
            json.dump(cal, f, indent=1)
        return
    now = datetime.now()
    hit = late = slipped = 0
    for it in prev["next10"]:
        done_now = _is_reached_now(it)
        try:
            eta = datetime.strptime(it["eta"], "%Y-%m-%d %H:%M")
        except Exception:
            continue
        if done_now:
            if now <= eta + timedelta(hours=2):
                hit += 1
            else:
                late += 1
        elif now > eta + timedelta(hours=4):
            slipped += 1
    total = len(prev["next10"])
    cal["runs"].append({"at": doc["generated"], "scored_forecast": prev.get("generated"),
                        "hit_on_time": hit, "late": late, "slipped": slipped, "total": total})
    cal["runs"] = cal["runs"][-60:]
    n = len(cal["runs"])
    if n:
        cal["rolling"] = {"hit_rate": round(sum(r["hit_on_time"] for r in cal["runs"]) / max(1, sum(r["total"] for r in cal["runs"])), 3),
                          "slip_rate": round(sum(r["slipped"] for r in cal["runs"]) / max(1, sum(r["total"] for r in cal["runs"])), 3)}
    with open(os.path.join(OUT, "calibration.json"), "w", encoding="utf-8") as f:
        json.dump(cal, f, indent=1)


def _is_reached_now(it):
    try:
        lanes, _ = _open_goals()
        st = lanes.get(it["agent"])
        if not st:
            return False
        # reached iff the goal text is NOT in the open list (fuzzy first-60 match)
        head = it["goal"][:60]
        return not any(head in t for t in st["open"])
    except Exception:
        return False


def _cycle_proposal(doc):
    """Ranked candidate goals for the next cycle - alignment hook for goal SETTING."""
    cands = _backlog_candidates()
    L = ["# Next-cycle proposal (pre-computed by forecast engine)", "",
         ("Generated: %s. Ratify/edit when the current cycle completes - do not draft cold. "
          "Ranked by predicted value: backlog cadence goals first, then successor patterns of just-closed work.") % doc["generated"], ""]
    for i, c in enumerate(cands[:10], 1):
        L.append("%d. **[%s] %s** - %s (source: %s)" % (i, c["agent"], c["ref"], c["text"], c["source"]))
    with open(os.path.join(OUT, "cycle-proposal.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def main():
    quiet = "--quiet" in sys.argv
    doc = refresh()
    if "--json" in sys.argv or not quiet:
        print(json.dumps({k: doc[k] for k in ("ok", "generated", "fleet", "throughput_goals_per_hour")}, indent=1))
        print("next10:")
        for it in doc["next10"]:
            print("  #%d [%s] %s ETA %s P=%.0f%%" % (it["rank"], it["agent"], it["goal"][:70], it["eta"], 100 * it["p_reached"]))
        for h in doc["horizons"]:
            print("  %-4s by %s: +%-3d goals -> fleet ~%.0f%%" % (h["label"], h["end"], h["completes"], h["fleet_pct"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())