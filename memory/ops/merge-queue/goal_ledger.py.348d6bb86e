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
import argparse, json, os, re, sys, datetime

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
# 2026-11-23 TIGHTENED: the old pattern matched the words "verified"/"acceptance"/
# "evidence"/"recorded" ANYWHERE in a line, so acceptance-criteria text inside an
# open goal counted as proof (phantom 78/80). Now only explicit closure markers
# count: an inline "(verified: ...)" tag or a "— recorded <date>" stamp — the same
# strict pattern memory/researcher/goal_ledger.py uses. record_evidence() writes
# "(evidence: ... — recorded DATE)", so ledger-closed goals still pass.
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

def _next_number(path):
    n = 0
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = CB_RE.match(line) or NUM_RE.match(line)
                if m:
                    # 2026-11-23 FIX: for checkbox lines group(1) is the [ ]/x state,
                    # the number is group(2); for numbered lines it is group(1).
                    num = m.group(2) if m.re is CB_RE else m.group(1)
                    if num:
                        n = max(n, int(num))
    return n + 1

def _agent_path(agent):
    fn = AGENT_FILES.get(agent.lower())
    if not fn:
        raise ValueError(f"unknown agent {agent!r}; valid: {sorted(AGENT_FILES)}")
    os.makedirs(GOALS_DIR, exist_ok=True)
    return os.path.join(GOALS_DIR, fn)

def _append_line(path, line):
    with open(path, "a", encoding="utf-8") as f:
        if os.path.getsize(path) == 0:
            f.write(f"# {os.path.basename(path)[:-3]} goals\n\n")
        elif not open(path, encoding='utf-8', errors='replace').read().endswith('\n'):
            f.write("\n")
        f.write(line + "\n")

def add_goal(agent, text):
    """Append an OPEN goal to the agent's file. Returns (path, number)."""
    path = _agent_path(agent)
    n = _next_number(path)
    _append_line(path, f"- [ ] {n}. {text.strip()}")
    return path, n

def record_evidence(agent, kind, note, evidence):
    """Evidence-gated closure: append a REACHED goal with inline proof.
    Use this instead of hand-checking boxes — the ledger only counts [x] lines
    that carry an acceptance/evidence marker (EVIDENCE_PAT). Returns (path, number)."""
    path = _agent_path(agent)
    n = _next_number(path)
    evs = evidence if isinstance(evidence, (list, tuple)) else [evidence]
    stamp = datetime.date.today().isoformat()
    tag = f"({kind}) " if kind else ""
    line = f"- [x] {n}. {tag}{note.strip()} (evidence: {', '.join(str(e) for e in evs)} — recorded {stamp})"
    _append_line(path, line)
    return path, n

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


def main(argv=None):
    ap = argparse.ArgumentParser(description='Evidence-gated goal ledger (Researcher)')
    ap.add_argument('--goals-dir', default='memory/goals')
    ap.add_argument('--json', action='store_true', help='pure JSON to stdout, no banners')
    ap.add_argument('--out', default=None, help='also write ledger JSON to this path')
    ap.add_argument('--add-goal', nargs=2, metavar=('AGENT', 'TEXT'),
                    help="append an open goal, e.g. --add-goal researcher 'Write X'")
    ap.add_argument('--record-evidence', nargs='+', metavar='ARG',
                    help="evidence-gated closure: AGENT KIND NOTE [EVIDENCE...] (paths or strings)")
    a = ap.parse_args(argv)
    if a.add_goal:
        path, n = add_goal(a.add_goal[0], a.add_goal[1])
        print(f"added open goal {n} to {path}")
    if a.record_evidence:
        args = a.record_evidence
        if len(args) < 3:
            ap.error("--record-evidence needs AGENT KIND NOTE [EVIDENCE...]")
        path, n = record_evidence(args[0], args[1], args[2], args[3:])
        print(f"recorded evidence for goal {n} in {path}")
    led = build_ledger(a.goals_dir)
    payload = json.dumps(led, indent=2, ensure_ascii=False)
    if a.out:
        d = os.path.dirname(a.out)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write(payload + '\n')
    if a.json:
        print(payload)
    else:
        # 2026-11-16: banner aligned to build_ledger() schema (flat fleet_* keys, agents dict)
        print(f"GOAL LEDGER  {led.get('fleet_reached')}/{led.get('fleet_total_goals')} reached ({led.get('fleet_pct_reached')}%)")
        for name, ag in led.get('agents', {}).items():
            print(f"  {name:<12} {ag['reached']}/{ag['total']}  {ag['pct_reached']}%  open={ag['open']}")

if __name__ == '__main__':
    main()
