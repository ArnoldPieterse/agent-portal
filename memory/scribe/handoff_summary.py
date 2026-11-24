#!/usr/bin/env python3
"""Cross-Agent Handoff Summary (Scribe goal, cycle 15).

Detects goals that changed seats between the last close-out snapshot
(memory/ops/goal-seat-snapshot.json, written by cycle_closeout.py) and the
current goal files, and writes a context summary for each handoff: what moved
from where to where, plus the goal text and evidence so the receiving agent
has full context.

Usage: python memory/scribe/handoff_summary.py [--cycle N] [--selftest]
Output: memory/synthesis/handoff-summary-<cycle>.md
"""
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
GOALS_DIR = BASE / "memory" / "goals"
SNAP = BASE / "memory" / "ops" / "goal-seat-snapshot.json"
SYNTH = BASE / "memory" / "synthesis"
AGENTS = ["orchestrator", "researcher", "verifier", "scribe",
          "designer", "builder", "archivist", "mechanic"]


def norm_title(title):
    return re.sub(r"[^a-z0-9]+", "", title.lower())[:40]


def current_seats():
    """{norm_title: (agent, num, title, desc, evidence)}"""
    seats = {}
    for ag in AGENTS:
        p = GOALS_DIR / (ag + ".md")
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for m in re.finditer(r"^(\d+)\.\s+\*\*(.+?)\*\*\s*-\s*(.+)$", text, re.M):
            num, title, first = int(m.group(1)), m.group(2).strip(), m.group(3)
            rest = text[m.end():].split("\n")
            desc_lines = [first]
            for line in rest:
                if re.match(r"^\d+\.\s", line):
                    break
                desc_lines.append(line)
            full = " ".join(l.strip() for l in desc_lines if l.strip())[:400]
            ev = re.search(r"\((?:verified|evidence):\s*([^)]+)\)", full)
            seats[norm_title(title)] = (ag, num, title, full, ev.group(1).strip() if ev else "")
    return seats


def load_snapshot():
    if not SNAP.exists():
        return None
    try:
        d = json.loads(SNAP.read_text(encoding="utf-8"))
        # snapshot stores {agent: [nums]} - rebuild title map from current files is
        # impossible for moved goals, so we match by goal number per agent instead.
        return d
    except Exception:
        return None


def detect_handoffs(prev_seats, cur_seats):
    """prev/cur: {agent: {norm_title: (ag,num,title,desc,evidence)}} -> list of dicts."""
    prev_flat = {}
    for ag, titles in prev_seats.items():
        for title, tup in titles.items():
            prev_flat[title] = tup
    out = []
    for ag, titles in cur_seats.items():
        for title, (ag2, num, t, d, ev) in titles.items():
            if title not in prev_flat:
                continue  # new goal, not a handoff
            from_ag = prev_flat[title][0]
            if from_ag != ag:
                out.append({"title": t, "from": from_ag, "to": ag,
                            "num": num, "desc": d, "evidence": ev})
    return out


def build_maps(seats_flat):
    """flat {norm_title:(agent,...)} -> {agent: {norm_title: tuple}}"""
    m = {a: {} for a in AGENTS}
    for title, tup in seats_flat.items():
        m[tup[0]][title] = tup
    return m


def generate(cycle_num):
    cur = current_seats()
    snap = load_snapshot()
    L = ["# Cross-Agent Handoff Summary - Cycle %d" % cycle_num, "",
         "Generated: %s" % datetime.now(timezone.utc).isoformat(timespec="seconds"), ""]
    if snap is None:
        L.append("_No previous seat snapshot found (run cycle_closeout.py first)._")
        return "\n".join(L), 0
    prev_flat = {}
    for ag, nums in snap.items():
        p = GOALS_DIR / (ag + ".md")
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for m2 in re.finditer(r"^(\d+)\.\s+\*\*(.+?)\*\*", text, re.M):
            if int(m2.group(1)) in nums:
                prev_flat[norm_title(m2.group(2))] = (ag, int(m2.group(1)), m2.group(2).strip(), "", "")
    handoffs = detect_handoffs(build_maps(prev_flat), build_maps(cur))
    if not handoffs:
        L.append("_No goal seat changes detected since the last close-out snapshot._")
        return "\n".join(L), 0
    for h in handoffs:
        L += ["## %s: %s -> %s" % (h["to"], h["from"], h["title"]), "",
              "Goal #%d now sits with **%s**." % (h["num"], h["to"]), "",
              "**Context carried over:**", "", "> " + h["desc"].replace("\n", " "), ""]
        if h["evidence"]:
            L += ["Evidence on record: %s" % h["evidence"], ""]
    return "\n".join(L), len(handoffs)


def selftest():
    ok = fail = 0
    def check(name, cond):
        nonlocal ok, fail
        print(("  PASS: " if cond else "  FAIL: ") + name)
        if cond: ok += 1
        else: fail += 1
    prev = build_maps({"alpha": ("builder", 3, "Alpha Goal", "d", "")})
    cur = build_maps({"alpha": ("scribe", 7, "Alpha Goal", "d2", "ev")})
    h = detect_handoffs(prev, cur)
    check("detects moved goal", len(h) == 1 and h[0]["from"] == "builder" and h[0]["to"] == "scribe")
    check("carries evidence", h[0]["evidence"] == "ev")
    same = detect_handoffs(prev, build_maps({"alpha": ("builder", 3, "Alpha Goal", "d", "")}))
    check("no false positive on same seat", same == [])
    newg = detect_handoffs(prev, build_maps({"beta": ("scribe", 9, "Beta Goal", "", "")}))
    check("new goal not a handoff", newg == [])
    print("Result: %d/%d passed" % (ok, ok + fail))
    return fail == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    cycle_num = 15
    if "--cycle" in sys.argv:
        i = sys.argv.index("--cycle")
        if i + 1 < len(sys.argv):
            cycle_num = int(sys.argv[i + 1])
    report, n = generate(cycle_num)
    SYNTH.mkdir(parents=True, exist_ok=True)
    out = SYNTH / ("handoff-summary-%d.md" % cycle_num)
    out.write_text(report, encoding="utf-8")
    print("Handoff summary written to: %s (%d handoffs)" % (out.relative_to(BASE), n))
