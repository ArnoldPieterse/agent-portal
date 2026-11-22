#!/usr/bin/env python3
"""
Task Re-Router (Goal #4 - Builder, cycle-10)
=============================================
When an agent is flagged unresponsive, find its pending tasks (open goals),
identify a capable alternative agent (by task type + current load), reassign
and log to decision-log.jsonl.

Usage:
  python memory/builder/task_rerouter.py --flagged <agent_id> [--dry-run]
  python memory/builder/task_rerouter.py --status-file memory/ops/roster_status.json [--dry-run]

Exit codes: 0=success, 1=no reassignments needed, 2=error
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent  # project root
AGENTS_JSON = BASE / "agents.json"
GOALS_DIR = BASE / "memory" / "goals"
DECISION_LOG = BASE / "memory" / "ops" / "decision-log.jsonl"
HANDOFF_DIR = BASE / "memory" / "builder"

# Capability mapping: keyword in goal text -> required agent trait
CAPABILITY_MAP = {
    "frontend": ["designer", "builder"],
    "css": ["designer"],
    "ui": ["designer", "builder"],
    "api": ["builder", "mechanic"],
    "endpoint": ["builder", "mechanic"],
    "server": ["mechanic", "builder"],
    "host": ["mechanic"],
    "vram": ["mechanic", "orchestrator"],
    "gpu": ["mechanic"],
    "research": ["researcher", "archivist"],
    "search": ["researcher", "archivist"],
    "knowledge": ["archivist"],
    "kb": ["archivist"],
    "synthesis": ["scribe"],
    "summar": ["scribe"],
    "decision-log": ["scribe", "builder"],
    "test": ["verifier"],
    "verify": ["verifier"],
    "evidence": ["verifier"],
    "script": ["builder"],
    "python": ["builder"],
    "automation": ["builder", "mechanic"],
    "schedtask": ["mechanic"],
    "schtask": ["mechanic"],
    "goal": ["orchestrator"],
    "roster": ["orchestrator"],
    "onboard": ["orchestrator"],
}


def load_agents():
    """Load agent profiles from agents.json."""
    with open(AGENTS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    return {a["id"]: a for a in data["agents"]}


def count_open_goals(agent_id):
    """Count open (unverified) goals for an agent from their goal file."""
    goal_file = GOALS_DIR / f"{agent_id}.md"
    if not goal_file.exists():
        return 0, []
    with open(goal_file, encoding="utf-8", errors="replace") as f:
        text = f.read()
    # Open goals are numbered lines without (verified:) tag
    open_goals = []
    for line in text.splitlines():
        m = re.match(r"^(\d+)\.\s+(.+)", line.strip())
        if m:
            goal_text = m.group(2)
            # Check if 'verified:' appears within ~500 chars after this line
            idx = text.find(line.strip())
            if idx == -1:
                continue
            snippet = text[idx:idx+500]
            if "(verified:" not in snippet:
                open_goals.append((int(m.group(1)), goal_text.strip()))
    return len(open_goals), open_goals


def infer_task_type(goal_text):
    """Infer task type from goal description text."""
    text_lower = goal_text.lower()
    scores = {}
    for keyword, agents in CAPABILITY_MAP.items():
        if keyword in text_lower:
            for a in agents:
                scores[a] = scores.get(a, 0) + 1
    return scores


def find_alternative(flagged_id, goal_text, all_agents):
    """Find the best alternative agent for a given task."""
    # Score candidates by capability match
    cap_scores = infer_task_type(goal_text)
    candidates = []
    for agent_id in all_agents:
        if agent_id == flagged_id:
            continue
        score = cap_scores.get(agent_id, 0)
        load, _ = count_open_goals(agent_id)
        # Prefer capable + less loaded
        effective_score = score * 10 - load
        candidates.append((effective_score, score, load, agent_id))
    candidates.sort(reverse=True)
    if not candidates:
        return None
    best = candidates[0]
    # Only reassign if there's at least some capability match OR the agent is very idle
    if best[1] == 0 and best[2] > 3:
        return None  # no capability match AND heavily loaded
    return best[3], best[1], best[2]


def log_decision(entry):
    """Append a decision to decision-log.jsonl."""
    DECISION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DECISION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def write_handoff(flagged_id, reassignments):
    """Write a handoff note for the Orchestrator to review."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    path = HANDOFF_DIR / f"task_reroute_{flagged_id}_{ts}.md"
    lines = [
        f"# Task Re-route: {flagged_id}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Agent `{flagged_id}` flagged unresponsive. Tasks reassigned:",
        "",
    ]
    for ra in reassignments:
        lines.append(f"- Goal #{ra['goal_num']}: {ra['goal_text'][:80]}")
        lines.append(f"  -> Reassigned to: **{ra['new_agent']}** (capability match: {ra['cap_score']}, load: {ra['load']} goals)")
    lines.append("")
    lines.append("_Auto-generated by task_rerouter.py. Orchestrator should ratify or adjust._")
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path.relative_to(BASE))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Reassign tasks from an unresponsive agent")
    parser.add_argument("--flagged", type=str, help="Agent ID that is flagged unresponsive")
    parser.add_argument("--status-file", type=str, help="JSON file with agent status (alternative to --flagged)")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without executing")
    args = parser.parse_args()

    # Determine flagged agent(s)
    flagged_ids = []
    if args.flagged:
        flagged_ids = [args.flagged]
    elif args.status_file:
        with open(args.status_file, encoding="utf-8") as f:
            status = json.load(f)
        flagged_ids = [a["id"] for a in status.get("agents", []) if not a.get("responsive", True)]
    else:
        parser.error("Must provide --flagged or --status-file")

    all_agents = load_agents()

    # Validate flagged agents exist
    valid_flagged = [fid for fid in flagged_ids if fid in all_agents]
    invalid = set(flagged_ids) - set(valid_flagged)
    if invalid:
        print(f"WARNING: unknown agent IDs: {invalid}", file=sys.stderr)
    if not valid_flagged:
        print("No valid flagged agents to reroute.")
        return 1

    total_reassigned = 0
    all_reassignments = []

    for fid in valid_flagged:
        open_count, open_goals = count_open_goals(fid)
        if not open_goals:
            print(f"{fid}: no open goals found - nothing to reroute.")
            continue

        print(f"\n{'='*60}")
        print(f"Agent: {fid} ({open_count} open goals)")
        print(f"{'='*60}")

        reassignments = []
        for goal_num, goal_text in open_goals:
            alt_id, cap_score, load = find_alternative(fid, goal_text, all_agents)
            if alt_id is None:
                print(f"  Goal #{goal_num}: NO suitable alternative (skipped)")
                print(f"    Task: {goal_text[:70]}")
                continue
            ra = {
                "goal_num": goal_num,
                "goal_text": goal_text,
                "new_agent": alt_id,
                "cap_score": cap_score,
                "load": load,
            }
            reassignments.append(ra)
            print(f"  Goal #{goal_num}: -> {alt_id} (match={cap_score}, load={load})")
            print(f"    Task: {goal_text[:70]}")

        total_reassigned += len(reassignments)
        all_reassignments.extend([{**ra, "from_agent": fid} for ra in reassignments])

    if not all_reassignments:
        print("\nNo reassignments needed.")
        return 1

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_reassigned} task(s) to reassign")
    print(f"{'='*60}")

    if args.dry_run:
        print("\n[DRY-RUN] No changes made.")
        return 0

    # Execute: write handoff + log decisions
    for fid in valid_flagged:
        fid_ras = [ra for ra in all_reassignments if ra["from_agent"] == fid]
        if not fid_ras:
            continue
        handoff_path = write_handoff(fid, fid_ras)
        print(f"\nHandoff written: {handoff_path}")

    # Log to decision-log
    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "builder",
        "type": "task_reroute",
        "flagged_agents": valid_flagged,
        "reassignments": [
            {"from": r["from_agent"], "to": r["new_agent"], "goal": r["goal_num"]}
            for r in all_reassignments
        ],
        "total": total_reassigned,
        "ok": True,
    }
    log_decision(log_entry)
    print(f"Decision logged: {DECISION_LOG.relative_to(BASE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())