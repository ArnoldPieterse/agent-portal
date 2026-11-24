#!/usr/bin/env python3
"""Cycle Transition Script (Builder goal 10, cycle 15).

Automates the full cycle close sequence:
(a) verify 100% completion, (b) archive old goals with timestamp,
(c) copy new goals from proposal file, (d) update TODO.md AGENT GOALS
section, (e) write transition log.
"""
import json
import re
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
GOALS_DIR = BASE / "memory" / "goals"
ARCHIVE_DIR = GOALS_DIR / "archive"
TODO_MD = BASE / "TODO.md"
TRANSITION_LOG = BASE / "memory" / "ops" / "cycle-transition-log.jsonl"
AGENTS = ["orchestrator", "researcher", "builder", "archivist",
          "scribe", "verifier", "designer", "mechanic"]


def verify_complete(goals_dir=None):
    """Count goals exactly like fleet_mode.py (numbered bold lines;
    reached = verified marker or existing pointer leaf)."""
    if goals_dir is None:
        goals_dir = GOALS_DIR
    total = reached = 0
    for ag in AGENTS:
        f = goals_dir / (ag + ".md")
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8", errors="replace").split("\n"):
            if not re.match(r"^\s*\d+\.\s+\*\*", line):
                continue
            total += 1
            if "(verified:" in line or "\u2014 recorded" in line:
                reached += 1
            else:
                pm = re.search(r"\(pointer:\s*([^)]+)\)", line)
                if pm and (BASE / pm.group(1).strip()).exists():
                    reached += 1
    return {"total": total, "reached": reached, "pct": (100.0 * reached / total) if total else 0.0}


def archive_old(cycle=None, stamp=None):
    goals_dir, archive_dir = GOALS_DIR, ARCHIVE_DIR
    stamp = stamp or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tag = "-cycle%s-prev" % cycle if cycle else ""
    archive_dir.mkdir(parents=True, exist_ok=True)
    done = []
    for ag in AGENTS:
        f = goals_dir / (ag + ".md")
        if not f.exists():
            continue
        dst = archive_dir / ("%s-%s%s.md" % (ag, stamp, tag))
        shutil.copy2(f, dst)
        done.append(str(dst.relative_to(BASE)))
    return done


def load_proposal(path):
    """Parse a proposal md: ### <Agent> sections with numbered goals."""
    text = Path(path).read_text(encoding="utf-8")
    per_agent = {}
    cur = None
    for line in text.splitlines():
        h = re.match(r"^###\s+(.+)$", line)
        if h:
            name = h.group(1).strip().lower()
            cur = next((a for a in AGENTS if a == name or a in name), None)
            per_agent.setdefault(cur, [])
            continue
        g = re.match(r"^\s*\d+\.\s+(.+)$", line)
        if g and cur:
            per_agent[cur].append(g.group(1).strip())
    return {a: v for a, v in per_agent.items() if a and v}


def write_new_goals(per_agent, cycle_no):
    written = []
    for agent in AGENTS:
        goals = per_agent.get(agent)
        if not goals:
            continue
        lines = ["# %s Goals - Cycle %d" % (agent.title(), cycle_no), ""]
        for i, g in enumerate(goals, 1):
            lines.append("%d. %s" % (i, g))
        (GOALS_DIR / ("%s.md" % agent)).write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(agent)
    return written


def update_todo(per_agent, cycle_no):
    """Mark old AGENT GOALS sections superseded; append the new one."""
    text = TODO_MD.read_text(encoding="utf-8")
    lines = text.splitlines()
    changed = False
    for i, l in enumerate(lines):
        if l.startswith("## AGENT GOALS") and "SUPERSEDED" not in l:
            lines[i] = l + " [SUPERSEDED by cycle %d transition]" % (cycle_no + 1)
            changed = True
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = ["", "## AGENT GOALS (set %s) - cycle %d" % (stamp, cycle_no + 1), ""]
    for agent in AGENTS:
        goals = per_agent.get(agent)
        if not goals:
            continue
        out.append("### %s (%d)" % (agent.title(), len(goals)))
        for i, g in enumerate(goals, 1):
            out.append("%d. [ ] %s" % (i, g))
        out.append("")
    new_text = "\n".join(lines) + "\n" + "\n".join(out) + "\n"
    TODO_MD.write_text(new_text, encoding="utf-8")
    return True


def log_transition(cycle_no, archived, proposal, written):
    TRANSITION_LOG.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": datetime.now(timezone.utc).isoformat(),
           "from_cycle": cycle_no, "to_cycle": cycle_no + 1,
           "archived": archived, "proposal": str(proposal),
           "new_goal_files": written}
    with open(TRANSITION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def transition(cycle_no, proposal, force=False):
    stats = verify_complete()
    if stats["pct"] < 100.0 and not force:
        raise SystemExit("cycle %d not complete: %.1f%% - use --force to override"
                         % (cycle_no, stats["pct"]))
    archived = archive_old(cycle_no)
    per_agent = load_proposal(proposal)
    written = write_new_goals(per_agent, cycle_no + 1)
    update_todo(per_agent, cycle_no)
    rec = log_transition(cycle_no, archived, proposal, written)
    return {"stats": stats, "archived": archived, "written": written, "log": rec}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycle", type=int, default=15)
    ap.add_argument("--proposal", required=True)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    res = transition(a.cycle, a.proposal, force=a.force)
    print("Transition %d -> %d: archived=%d new_files=%s log=%s"
          % (a.cycle, a.cycle + 1, len(res["archived"]), res["written"], "ok"))


def selftest():
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="ct_"))
    goals = tmp / "goals"; goals.mkdir()
    (goals / "scribe.md").write_text(
        "1. **Old Goal** - done (verified: 2026-11-24 - x)\n", encoding="utf-8")
    prop = tmp / "prop.md"
    prop.write_text("### Scribe\n1. **New One** - a\n2. **New Two** - b\n"
                    "### Builder\n1. **New Three** - c\n", encoding="utf-8")
    todo = tmp / "TODO.md"
    todo.write_text("## AGENT GOALS (set old)\n1. stale\n", encoding="utf-8")
    logf = tmp / "log.jsonl"
    g = sys.modules[__name__]
    g.GOALS_DIR, g.ARCHIVE_DIR = goals, goals / "archive"
    g.TODO_MD, g.TRANSITION_LOG = todo, logf
    res = transition(9, prop)
    arch = list((goals / "archive").glob("scribe-*cycle9-prev.md"))
    new_s = (goals / "scribe.md").read_text(encoding="utf-8")
    td = todo.read_text(encoding="utf-8")
    ok = (len(res["archived"]) == 1 and len(arch) == 1
          and new_s.count("\n1. ") >= 1 and "New One" in new_s and "SUPERSEDED" in td
          and "cycle 10" in td and logf.exists())
    print("Result: %s" % ("PASS" if ok else "FAIL"))
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    main()
