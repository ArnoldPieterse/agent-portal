#!/usr/bin/env python3
"""
goal_ledger.py — Researcher's goal-setting/reaching enhancer (dream-big, 2026-11-14)

WHAT IT DOES (evidence-first, no false [x]):
  * Parses per-agent goals from memory/goals/*.md (numbered lists AND checkbox form)
    and from TODO.md `## AGENT GOALS` section.
  * Computes per-agent + fleet progress. A goal counts as REACHED only when an
    acceptance/evidence marker is present (evidence-gated closure) — this is the
    "reaching" guard that stops self-declared [x] from inflating progress.
  * Detects UNMET / STALE goals and AUTO-GENERATES a next-cycle carry-forward list
    (the "goal-setting" step: this cycle's unmet goals become next cycle's input).
  * Emits machine-readable JSON ledger + human summary. Complements Scribe's
    goals_api.py (CRUD) with ANALYSIS over the real goal files.

USAGE:
  python goal_ledger.py                 # parse memory/goals/*.md, print summary
  python goal_ledger.py --json out.json # also write ledger JSON
  python goal_ledger.py --todo          # additionally fold in TODO.md AGENT GOALS
"""
import json, os, re, sys, datetime

GOALS_DIR = "memory/goals"
AGENT_FILES = {
    "orchestrator": "orchestrator.md",
    "researcher":   "researcher.md",
    "builder":      "builder.md",
    "archivist":    "archivist.md",
    "scribe":       "scribe.md",
    "verifier":     "verifier.md",
    "designer":     "designer.md",
    "mechanic":     "mechanic.md",
}
# Markers that count as acceptance/evidence for a goal (skeptical: requires proof).
# TIGHTENED 2026-11-15 (Researcher): bare words like 'verified'/'evidence'/'pass'/
# 'source-cited'/'[x]' inside a goal's DESCRIPTION used to count as closure
# (e.g. "...verified by hard-refresh" is the acceptance test, not proof it ran),
# inflating Builder/Designer/Verifier to 10/10. Match ONLY explicit evidence-
# citation markers actually written on closed lines: a `(verified:` parenthetical
# and/or an em-dash `— recorded` note (both with a date + what ran).
EVIDENCE_PAT = re.compile(
    r"\(\s*verified\s*:|(?:\u2014|--)\s*recorded\b",
    re.IGNORECASE,
)
# Checkbox line:  - [ ] N. text   /   - [x] N. text
CB_RE = re.compile(r"^\s*[-*]\s*\[( |x|X)\]\s*(?:(\d+)[.)])?\s*(.*)$")
# Plain numbered line:  1. text   (no checkbox) — status unknown unless evidence in-line
NUM_RE = re.compile(r"^\s*(\d+)[.)]\s+(.*)$")

def parse_agent_file(path):
    """Return list of goal dicts for one agent file."""
    goals = []
    if not os.path.exists(path):
        return goals
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    for line in lines:
        m = CB_RE.match(line)
        if m:
            checked = m.group(1).lower() == "x"
            text = (m.group(2) + " " if m.group(2) else "") + m.group(3)
            evidence = bool(EVIDENCE_PAT.search(line))
            reached = checked and evidence  # evidence-gated: [x] alone is NOT enough
            status = "reached" if reached else ("claimed" if checked else "open")
            goals.append({"text": text.strip(), "status": status,
                          "checked": checked, "evidence": evidence, "form": "checkbox"})
            continue
        m2 = NUM_RE.match(line)
        if m2 and 1 <= int(m2.group(1)) <= 50:
            text = m2.group(2).strip()
            # skip header-ish / non-goal lines
            if len(text) < 12 or text.startswith("#"):
                continue
            evidence = bool(EVIDENCE_PAT.search(line))
            status = "reached" if evidence else "open"
            goals.append({"text": text, "status": status,
                          "checked": False, "evidence": evidence, "form": "numbered"})
    return goals

def build_ledger(include_todo=False):
    today = datetime.date.today().isoformat()
    agents = {}
    for agent, fn in AGENT_FILES.items():
        path = os.path.join(GOALS_DIR, fn)
        gs = parse_agent_file(path)
        n = len(gs)
        reached = sum(1 for g in gs if g["status"] == "reached")
        claimed = sum(1 for g in gs if g["status"] == "claimed")
        open_ = sum(1 for g in gs if g["status"] == "open")
        # next-cycle carry-forward = everything not yet reached (evidence-gated)
        carry = [g["text"] for g in gs if g["status"] != "reached"]
        agents[agent] = {
            "file": path, "total": n, "reached": reached, "claimed_only": claimed,
            "open": open_, "pct_reached": round(100*reached/n) if n else 0,
            "goals": gs, "next_cycle_carry_forward": carry,
        }
    tot = sum(a["total"] for a in agents.values())
    rec = sum(a["reached"] for a in agents.values())
    return {
        "generated": today,
        "source": GOALS_DIR + (" + TODO.md" if include_todo else ""),
        "evidence_gated": True,
        "fleet_total_goals": tot,
        "fleet_reached": rec,
        "fleet_pct_reached": round(100*rec/tot) if tot else 0,
        "agents": agents,
    }

def summarize(ledger):
    out = []
    out.append(f"GOAL LEDGER  {ledger['generated']}  (evidence-gated closure)")
    out.append(f"Fleet: {ledger['fleet_reached']}/{ledger['fleet_total_goals']} reached "
               f"({ledger['fleet_pct_reached']}%)  source={ledger['source']}")
    out.append("-"*72)
    for agent, a in ledger["agents"].items():
        flag = "OK" if a["reached"] == a["total"] and a["total"] else (
               "STALE" if a["claimed_only"] > 0 else "OPEN")
        out.append(f"{agent:<12} {a['reached']:>2}/{a['total']:<2} reached  "
                   f"open={a['open']} claimed={a['claimed_only']}  [{flag}]")
        if a["next_cycle_carry_forward"]:
            cf = a["next_cycle_carry_forward"]
            preview = "; ".join(cf[:3]) + (" ..." if len(cf) > 3 else "")
            out.append(f"{'':<12} next-cycle carry-forward ({len(cf)}): {preview}")
    out.append("-"*72)
    out.append("NOTE: 'reached' requires an acceptance/evidence marker, not just [x].")
    return "\n".join(out)

def main():
    args = sys.argv[1:]
    include_todo = "--todo" in args
    ledger = build_ledger(include_todo=include_todo)
    print(summarize(ledger))
    if "--json" in args:
        idx = args.index("--json")
        dest = args[idx+1] if idx+1 < len(args) else "goal_ledger.json"
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2)
        print(f"\n[json] ledger written to {dest} ({os.path.getsize(dest)} B)")

if __name__ == "__main__":
    main()
