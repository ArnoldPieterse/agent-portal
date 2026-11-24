#!/usr/bin/env python3
"""Mode Decision Brief (Scribe goal, cycle 15).

For each fleet-mode transition recorded in memory/ops/mode-transitions.jsonl,
write a one-paragraph brief explaining the decision: what changed, the metrics
that drove it, and why the new mode follows from the decision rules
(WORK while goals remain open; MAINTENANCE within 6h of completion; IDLE after).

Usage: python memory/scribe/mode_decision_brief.py [--selftest]
Output: memory/synthesis/mode-decision-briefs.md (regenerated whole each run)
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TRANSITIONS = BASE / "memory" / "ops" / "mode-transitions.jsonl"
OUT = BASE / "memory" / "synthesis" / "mode-decision-briefs.md"

RULES = ("Fleet mode follows three rules: WORK while any goal is open (pct < 100); "
         "MAINTENANCE once all goals are reached but the fleet was active within the "
         "last 6 hours; IDLE after 6 quiet hours.")


def load_transitions():
    if not TRANSITIONS.exists():
        return []
    out = []
    for line in TRANSITIONS.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        d["from_mode"] = d.get("from_mode") or d.get("from")
        d["to_mode"] = d.get("to_mode") or d.get("to")
        if d.get("from_mode") and d.get("to_mode"):
            out.append(d)
    return out


def brief_for(t):
    frm = t.get("from_mode") or t.get("from")
    to = t.get("to_mode") or t.get("to")
    ts = t.get("ts", "unknown time")
    trigger = t.get("trigger", "")
    open_n = t.get("goal_count_open")
    bits = []
    if trigger:
        bits.append(trigger.replace(",", ", "))
    if open_n is not None:
        bits.append("%d goal(s) still open" % open_n)
    context = "; ".join(bits) if bits else "no metrics captured at transition time"
    why = {
        ("IDLE", "WORK"): "activity resumed and open goals were detected, so the fleet returns to goal work",
        ("MAINTENANCE", "WORK"): "open goals were re-detected, overriding the maintenance window",
        ("WORK", "MAINTENANCE"): "all goals reached 100% while the fleet was still active, opening the maintenance window",
        ("WORK", "IDLE"): "all goals reached and the quiet threshold elapsed",
        ("MAINTENANCE", "IDLE"): "the maintenance window closed without new work; the fleet idles",
        ("IDLE", "MAINTENANCE"): "maintenance tasks were queued while the fleet was idle",
    }.get((frm, to), "the decision rules re-evaluated and selected a different mode")
    return ("At %s the fleet moved %s -> %s. At that moment: %s. Decision: %s. %s"
            % (ts, frm, to, context, why, RULES))


def generate():
    trans = load_transitions()
    L = ["# Mode Decision Briefs", "", "Regenerated: %s | transitions on file: %d"
         % (datetime.now(timezone.utc).isoformat(timespec="seconds"), len(trans)), ""]
    if not trans:
        L.append("_No mode transitions recorded yet._")
    for i, t in enumerate(trans, 1):
        L.append("## Transition %d" % i)
        L.append("")
        L.append(brief_for(t))
        L.append("")
    return "\n".join(L)


def selftest():
    ok = fail = 0
    def check(name, cond):
        nonlocal ok, fail
        print(("  PASS: " if cond else "  FAIL: ") + name)
        if cond: ok += 1
        else: fail += 1
    t1 = {"from_mode": "IDLE", "to_mode": "WORK", "ts": "2026-11-24T01:00:00Z",
          "trigger": "goal_pct=30.0,elapsed=0.01h", "goal_count_open": 56}
    b = brief_for(t1)
    check("brief names both modes", "IDLE -> WORK" in b)
    check("brief carries metrics", "56 goal(s) still open" in b and "30.0" in b)
    check("brief explains rule", "open goals were detected" in b or "returns to goal work" in b)
    t2 = {"from": "WORK", "to": "MAINTENANCE"}   # legacy key shape, no metrics
    b2 = brief_for(t2)
    check("legacy keys handled", "WORK -> MAINTENANCE" in b2 and "no metrics captured" in b2)
    rep = generate()
    check("report has header + rules", "# Mode Decision Briefs" in rep and RULES[:30] in rep)
    print("Result: %d/%d passed" % (ok, ok + fail))
    return fail == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(generate(), encoding="utf-8")
    print("Mode decision briefs written to: %s (%d transitions)"
          % (OUT.relative_to(BASE), len(load_transitions())))
