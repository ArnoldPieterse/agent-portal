#!/usr/bin/env python3
"""Cycle Close-Out Report Generator (Scribe goal #1, cycle 15).

At cycle close, generates a structured report:
- Goals completed (by agent, with evidence refs)
- Blockers encountered + resolution time
- Key decisions made
- Efficiency metrics

Usage: python memory/scribe/cycle_closeout.py [--cycle N]
Output: memory/synthesis/closeout-cycle{N}-YYYY-MM-DD.md
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent  # project root
GOALS_DIR = BASE / "memory" / "goals"
OPS_DIR = BASE / "memory" / "ops"
SYNTH_DIR = BASE / "memory" / "synthesis"

AGENTS = [
    "orchestrator", "researcher", "verifier", "scribe",
    "designer", "builder", "archivist", "mechanic",
]


def parse_goals_file(agent: str) -> list[dict]:
    """Parse an agent's goals file, extracting goal status + evidence refs."""
    path = GOALS_DIR / f"{agent}.md"
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    goals = []
    # Match numbered goals: "N. **Title** - description ... (verified: ...)"
    pattern = re.compile(
        r"^(\d+)\.\s+\*\*(.+?)\*\*\s*-\s*(.+)$", re.MULTILINE
    )
    for match in pattern.finditer(text):
        num = int(match.group(1))
        title = match.group(2).strip()
        desc_start = match.start(3)
        # Get the full line/paragraph for this goal
        lines_after = text[desc_start:].split("\n")
        desc_lines = [lines_after[0]]
        for line in lines_after[1:]:
            if re.match(r"^\d+\.\s", line):
                break
            desc_lines.append(line)
        full_desc = " ".join(l.strip() for l in desc_lines if l.strip())

        # Check for verified marker
        verified_match = re.search(r"\(verified:\s*([^)]+)\)", full_desc)
        is_verified = bool(verified_match)
        evidence = verified_match.group(1).strip() if verified_match else ""

        goals.append({
            "num": num,
            "title": title,
            "status": "completed" if is_verified else "open",
            "evidence": evidence,
            "desc": full_desc[:300],
        })
    return goals


def parse_blockers() -> list[dict]:
    """Parse memory/ops/blockers.md for blocker entries."""
    path = OPS_DIR / "blockers.md"
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    blockers = []

    # Match [OPS-NOTE date] or [NEEDS-HUMAN date] entries
    entry_pattern = re.compile(
        r"^##\s+\[(OPS-NOTE|NEEDS-HUMAN)\s+(\d{4}-\d{2}-\d{2})\]\s*(.+?)(?=^##\s|^$)",
        re.MULTILINE | re.DOTALL,
    )
    for m in entry_pattern.finditer(text):
        btype = m.group(1)
        date = m.group(2)
        title = m.group(3).strip().split("\n")[0].strip()

        # Try to find resolution info
        body = m.group(3)
        resolved = "resolved" in body.lower() or "status: resolved" in body.lower()
        resolution_time = ""
        res_match = re.search(r"(?:resolved|closed)\s*[:(]\s*([^\n]+)", body, re.IGNORECASE)
        if res_match:
            resolution_time = res_match.group(1).strip()

        blockers.append({
            "type": btype,
            "date": date,
            "title": title[:200],
            "resolved": resolved,
            "resolution_time": resolution_time,
        })

    # Also match simpler format: lines starting with "- **Blocker" or similar
    simple_pattern = re.compile(r"^[-*]\s+\*\*(.+?)\*\*[:\-]\s*(.+?)(?=^[-*]|$)", re.MULTILINE)
    for m in simple_pattern.finditer(text):
        title = m.group(1).strip()
        desc = m.group(2).strip()
        if "blocker" in title.lower() or "block" in title.lower():
            blockers.append({
                "type": "simple",
                "date": "",
                "title": f"{title}: {desc[:150]}",
                "resolved": False,
                "resolution_time": "",
            })

    return blockers


def parse_decisions(cycle_start: str = "") -> list[dict]:
    """Parse decision-log.jsonl for recent decisions."""
    path = OPS_DIR / "decision-log.jsonl"
    if not path.exists():
        return []

    decisions = []
    try:
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        for line in lines[-50:]:  # last 50 entries
            if line.strip():
                try:
                    d = json.loads(line)
                    decisions.append(d)
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    return decisions


def compute_efficiency(goals_by_agent: dict, blockers: list) -> dict:
    """Compute basic efficiency metrics."""
    total_goals = sum(len(g) for g in goals_by_agent.values())
    completed = sum(1 for goals in goals_by_agent.values() for g in goals if g["status"] == "completed")
    open_count = total_goals - completed
    pct = (completed / total_goals * 100) if total_goals > 0 else 0

    return {
        "total_goals": total_goals,
        "completed": completed,
        "open": open_count,
        "completion_pct": round(pct, 1),
        "blockers_total": len(blockers),
        "blockers_resolved": sum(1 for b in blockers if b["resolved"]),
    }


def generate_report(cycle_num: int) -> str:
    """Generate the full close-out report as markdown."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    goals_by_agent = {}
    for agent in AGENTS:
        goals_by_agent[agent] = parse_goals_file(agent)

    blockers = parse_blockers()
    decisions = parse_decisions()
    efficiency = compute_efficiency(goals_by_agent, blockers)

    lines = []
    lines.append(f"# Cycle {cycle_num} Close-Out Report - {date_str}")
    lines.append("")
    lines.append(f"**Generated:** {now.isoformat()}")
    lines.append(f"**Fleet completion:** {efficiency['completed']}/{efficiency['total_goals']} "
                 f"({efficiency['completion_pct']}%)")
    lines.append("")

    # Section 1: Goals by agent
    lines.append("## Goals Completed by Agent")
    lines.append("")
    for agent in AGENTS:
        goals = goals_by_agent[agent]
        if not goals:
            continue
        completed = [g for g in goals if g["status"] == "completed"]
        open_goals = [g for g in goals if g["status"] != "completed"]
        lines.append(f"### {agent.capitalize()} ({len(completed)}/{len(goals)} complete)")
        lines.append("")
        for g in completed:
            ev = f" - evidence: {g['evidence']}" if g["evidence"] else ""
            lines.append(f"- [x] #{g['num']} **{g['title']}**{ev}")
        for g in open_goals:
            lines.append(f"- [ ] #{g['num']} **{g['title']}**")
        lines.append("")

    # Section 2: Blockers
    lines.append("## Blockers Encountered")
    lines.append("")
    if blockers:
        for b in blockers:
            status = "RESOLVED" if b["resolved"] else "OPEN"
            date_part = f" ({b['date']})" if b["date"] else ""
            res_part = f" - resolution: {b['resolution_time']}" if b["resolution_time"] else ""
            lines.append(f"- [{status}] [{b['type']}]{date_part} {b['title']}{res_part}")
    else:
        lines.append("- No blockers recorded.")
    lines.append("")

    # Section 3: Key decisions
    lines.append("## Key Decisions (last 50)")
    lines.append("")
    if decisions:
        for d in decisions[-10:]:  # show last 10 in report
            ts = d.get("ts", "unknown")[:19]
            agent = d.get("agent", "?")
            dtype = d.get("type", "?")
            extra = ""
            if "runbook" in d:
                extra = f" runbook={d['runbook']}"
            elif "action" in d:
                extra = f" action={d['action'][:80]}"
            lines.append(f"- {ts} | {agent} | {dtype}{extra}")
    else:
        lines.append("- No decisions logged.")
    lines.append("")

    # Section 4: Efficiency metrics
    lines.append("## Efficiency Metrics")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total goals tracked | {efficiency['total_goals']} |")
    lines.append(f"| Completed | {efficiency['completed']} |")
    lines.append(f"| Open | {efficiency['open']} |")
    lines.append(f"| Completion rate | {efficiency['completion_pct']}% |")
    lines.append(f"| Blockers (total) | {efficiency['blockers_total']} |")
    lines.append(f"| Blockers resolved | {efficiency['blockers_resolved']} |")
    lines.append("")

    # Section 5: Recommendations
    lines.append("## Recommendations for Next Cycle")
    lines.append("")
    open_agents = [a for a in AGENTS if any(g["status"] != "completed" for g in goals_by_agent.get(a, []))]
    if open_agents:
        lines.append(f"- Focus on completing open goals in: {', '.join(open_agents)}")
    if efficiency["blockers_resolved"] < efficiency["blockers_total"]:
        lines.append("- Address remaining open blockers before starting new work")
    if efficiency["completion_pct"] >= 90:
        lines.append("- Fleet near full completion - consider mode transition to MAINTENANCE/IDLE")
    else:
        lines.append(f"- {efficiency['open']} goals remain open; prioritize by dependency order")
    lines.append("")

    return "\n".join(lines)


def main():
    cycle_num = 15
    if "--cycle" in sys.argv:
        idx = sys.argv.index("--cycle")
        if idx + 1 < len(sys.argv):
            cycle_num = int(sys.argv[idx + 1])

    report = generate_report(cycle_num)

    SYNTH_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = SYNTH_DIR / f"closeout-cycle{cycle_num}-{date_str}.md"
    out_path.write_text(report, encoding="utf-8")

    print(f"Close-out report written to: {out_path.relative_to(BASE)}")
    print(f"Cycle {cycle_num}: {report.split(chr(10))[3] if len(report.split(chr(10))) > 3 else 'see file'}")


if __name__ == "__main__":
    main()
