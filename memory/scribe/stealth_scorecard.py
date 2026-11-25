#!/usr/bin/env python3
"""Stealth $ scorecard generator + self-test.
Reads memory/scribe/stealth-ledger-data.json, computes revenue/effort ($/agent-min)
per workflow and overall, applies kill/scale calls, self-verifies the math,
and emits the Weekly Scorecard markdown block. Run: python memory/scribe/stealth_scorecard.py
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "stealth-ledger-data.json"

def load():
    return json.loads(DATA.read_text(encoding="utf-8"))

def compute(d):
    """Aggregate per-workflow revenue + effort across all days; compute $/effort."""
    kill = d["kill_threshold_dollar_per_min"]
    scale = d["scale_threshold_dollar_per_min"]
    agg = {}  # wf id -> {name, revenue, effort}
    total_rev = 0.0
    total_effort = 0.0
    for day in d["days"]:
        for w in day["workflows"]:
            a = agg.setdefault(w["id"], {"name": w["name"], "revenue": 0.0, "effort": 0})
            a["revenue"] += w["revenue_usd"]
            a["effort"] += w["effort_agent_min"]
        total_rev += day["revenue_usd"]
    for a in agg.values():
        total_effort += a["effort"]
    rows = []
    for wid, a in agg.items():
        dpe = (a["revenue"] / a["effort"]) if a["effort"] else 0.0
        # kill/scale call: only decide once revenue exists; otherwise HOLD pending Day-N
        if a["revenue"] <= 0:
            call = "HOLD (no revenue yet - re-evaluate at Day %d)" % d["scorecard_due_day"]
        elif dpe < kill:
            call = "KILL (< $%d/min)" % kill
        elif dpe > scale:
            call = "SCALE (> $%d/min)" % scale
        else:
            call = "KEEP (within band)"
        rows.append({"id": wid, "name": a["name"], "revenue": a["revenue"],
                     "effort": a["effort"], "dpe": dpe, "call": call})
    # rank by $/effort desc (ties -> revenue desc)
    rows.sort(key=lambda r: (-r["dpe"], -r["revenue"]))
    overall_dpe = (total_rev / total_effort) if total_effort else 0.0
    return rows, {"total_revenue": total_rev, "total_effort": total_effort,
                  "overall_dpe": overall_dpe, "kill": kill, "scale": scale}

def selftest(rows, tot):
    """Assert the math is internally consistent."""
    # 1) sum of per-workflow revenue == total revenue
    assert abs(sum(r["revenue"] for r in rows) - tot["total_revenue"]) < 1e-9, "revenue sum mismatch"
    # 2) sum of per-workflow effort == total effort
    assert sum(r["effort"] for r in rows) == tot["total_effort"], "effort sum mismatch"
    # 3) each row dpe == revenue/effort
    for r in rows:
        expect = (r["revenue"] / r["effort"]) if r["effort"] else 0.0
        assert abs(r["dpe"] - expect) < 1e-9, "dpe mismatch %s" % r["id"]
    # 4) overall dpe == total_revenue/total_effort
    expect = (tot["total_revenue"] / tot["total_effort"]) if tot["total_effort"] else 0.0
    assert abs(tot["overall_dpe"] - expect) < 1e-9, "overall dpe mismatch"
    return True

def render(rows, tot, d):
    L = []
    L.append("## Weekly Scorecard")
    L.append("*(first scorecard due end of Day %d = 2026-12-02; computed by stealth_scorecard.py)*" % d["scorecard_due_day"])
    L.append("")
    L.append("| Rank | Workflow | Revenue $ | Effort (agent-min) | $/effort | Call |")
    L.append("|------|----------|-----------|-------------------|----------|------|")
    for i, r in enumerate(rows, 1):
        L.append("| %d | %s: %s | $%.2f | %d | $%.2f/min | %s |" % (
            i, r["id"], r["name"], r["revenue"], r["effort"], r["dpe"], r["call"]))
    L.append("")
    L.append("**Overall:** $%.2f revenue / %d agent-min = **$%.2f/min** across %d workflows." % (
        tot["total_revenue"], tot["total_effort"], tot["overall_dpe"], len(rows)))
    L.append("")
    L.append("**Method:** $/effort = total_revenue / total_agent_minutes_spent_on_workflow. "
             "Kill if < $%d/min after %d days; scale if > $%d/min." % (tot["kill"], d["scorecard_due_day"], tot["scale"]))
    return "\n".join(L)

def main():
    d = load()
    rows, tot = compute(d)
    ok = selftest(rows, tot)
    md = render(rows, tot, d)
    print(md)
    print("\n[SELFTEST] math consistent: %s | rows=%d total_rev=$%.2f total_effort=%d overall=$%.2f/min" % (
        "PASS" if ok else "FAIL", len(rows), tot["total_revenue"], tot["total_effort"], tot["overall_dpe"]))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
