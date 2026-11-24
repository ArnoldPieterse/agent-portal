#!/usr/bin/env python3
"""
cycle_skeleton.py — Cycle Proposal Skeleton Generator (Orchestrator goal #10)

At cycle close, auto-generate next-cycle proposal skeleton from:
  (a) completed goals (what worked) - from current cycle goal files
  (b) open patterns from decision-log.jsonl
  (c) round_topic.json queue

Usage: python memory/orchestrator/cycle_skeleton.py [--dry-run] [--cycle N] [--source-cycle N]
Writes to: memory/goals/cycle{N+1}-skeleton.md
"""
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path

def detect_cycle(goal_dir):
    """Detect current cycle from goal file headers."""
    best = 0
    for f in goal_dir.glob("*.md"):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")[:300]
        except Exception:
            continue
        m = re.search(r"Cycle\s+(\d+)", text)
        if m:
            best = max(best, int(m.group(1)))
    return best

def load_closed_sigs(closed_path):
    """Load closed topic signatures for dedup."""
    sigs = set()
    titles = set()
    if closed_path.exists():
        try:
            data = json.loads(closed_path.read_text(encoding="utf-8"))
            for entry in data:
                sigs.add(entry.get("sig", ""))
                t = entry.get("text", "").replace("*", "").strip()[:50].lower()
                if t:
                    titles.add(t)
        except Exception:
            pass
    return sigs, titles

def extract_completed_goals(goal_dir):
    """Extract verified goal titles from current cycle goal files."""
    completed = []
    for f in sorted(goal_dir.glob("*.md")):
        agent = f.stem.lower()
        text = f.read_text(encoding="utf-8", errors="ignore")
        lines = text.split("\n")
        for i, line in enumerate(lines):
            m = re.match(r"^\s*\d+\.\s*\*\*(.+?)\*\*", line)
            if not m:
                continue
            title = m.group(1).strip()
            block = "\n".join(lines[i:i+3])
            if "verified:" in block.lower():
                completed.append({"title": title, "agent": agent, "source": str(f)})
    return completed

def extract_open_goals(goal_dir):
    """Extract un-verified (still open) goal titles from current cycle."""
    open_goals = []
    for f in sorted(goal_dir.glob("*.md")):
        agent = f.stem.lower()
        text = f.read_text(encoding="utf-8", errors="ignore")
        lines = text.split("\n")
        for i, line in enumerate(lines):
            m = re.match(r"^\s*\d+\.\s*\*\*(.+?)\*\*", line)
            if not m:
                continue
            title = m.group(1).strip()
            block = "\n".join(lines[i:i+3])
            if "verified:" not in block.lower():
                open_goals.append({"title": title, "agent": agent})
    return open_goals

def extract_decision_patterns(decision_log):
    """Extract recurring event types from decision log."""
    if not decision_log.exists():
        return []
    patterns = {}
    for line in decision_log.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except Exception:
            continue
        t = entry.get("type", entry.get("detail", ""))
        if not t:
            continue
        key = t[:30]
        patterns.setdefault(key, {"count": 0, "agents": set()})
        patterns[key]["count"] += 1
        agent = entry.get("agent", "unknown")
        patterns[key]["agents"].add(agent)
    result = []
    for key, info in sorted(patterns.items(), key=lambda x: -x[1]["count"]):
        if info["count"] >= 3:
            result.append({"type": key, "count": info["count"],
                           "agents": ", ".join(sorted(info["agents"]))})
    return result

def load_round_topic(topic_path):
    """Load round topic queue."""
    if not topic_path.exists():
        return {"current": {}, "queue": [], "past": []}
    try:
        return json.loads(topic_path.read_text(encoding="utf-8"))
    except Exception:
        return {"current": {}, "queue": [], "past": []}

def generate_skeleton(goal_dir, decision_log, topic_path, cycle_num=None, source_cycle=None):
    """Generate the skeleton markdown."""
    if cycle_num is None:
        cycle_num = detect_cycle(goal_dir)
    next_cycle = cycle_num + 1
    src = source_cycle if source_cycle else cycle_num

    closed_sigs, closed_titles = load_closed_sigs(goal_dir / "closed_topics.json")
    completed = extract_completed_goals(goal_dir)
    open_goals = extract_open_goals(goal_dir)
    patterns = extract_decision_patterns(decision_log)
    topic_data = load_round_topic(topic_path)

    stubs = []
    seen_titles = set()
    def is_dup(title):
        t = title.lower()[:50]
        if t in closed_titles:
            return True
        for st in seen_titles:
            if t[:30] == st[:30]:
                return True
        return False

    # Source (a): extend completed capabilities
    by_agent = {}
    for g in completed:
        by_agent.setdefault(g["agent"], []).append(g)
    for agent, goals in sorted(by_agent.items()):
        if len(stubs) >= 10:
            break
        for g in goals[:2]:
            title = f"Extend: {g['title']}"
            if is_dup(g["title"]):
                continue
            seen_titles.add(g["title"].lower())
            src_file = Path(g["source"]).name
            stubs.append({
                "title": title,
                "pillar": agent.capitalize(),
                "rationale": f"Built in cycle {src} ({src_file}). Next step: production hardening or extension.",
            })

    # Source (b): recurring decision-log patterns
    for p in patterns[:4]:
        if len(stubs) >= 10:
            break
        title = f"Harden {p['type']} pipeline"
        if is_dup(p["type"]):
            continue
        seen_titles.add(p["type"].lower())
        stubs.append({
            "title": title,
            "pillar": "Automation",
            "rationale": f"Recurring {p['type']} events ({p['count']}x) across agents: {p['agents']}. Build monitoring/self-healing.",
        })

    # Source (c): round topic queue items
    for q in topic_data.get("queue", [])[:3]:
        if len(stubs) >= 10:
            break
        qt = q if isinstance(q, str) else q.get("topic", "Untitled")
        if is_dup(qt):
            continue
        seen_titles.add(qt.lower())
        stubs.append({
            "title": f"Pursue queued topic: {qt}",
            "pillar": "Roadmap",
            "rationale": f"From round_topic.json queue. Description: {str(q.get('description', ''))[:100]}",
        })

    # Source (d): carry-over open goals (unfinished from current cycle)
    for g in open_goals[:5]:
        if len(stubs) >= 10:
            break
        title = f"Complete: {g['title']}"
        if is_dup(g["title"]):
            continue
        seen_titles.add(g["title"].lower())
        stubs.append({
            "title": title,
            "pillar": g["agent"].capitalize(),
            "rationale": f"Open in cycle {src} ({g['agent']}). Carry forward to complete.",
        })

    assert len(stubs) >= 5, f"Only generated {len(stubs)} stubs - need >=5"

    # Assemble markdown
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# Cycle {next_cycle} Proposal Skeleton",
             f"Generated: {now} by cycle_skeleton.py (auto)",
             f"Source data: {len(completed)} completed goals, {len(patterns)} decision patterns, "
             f"{len(topic_data.get('queue', []))} queue items"]
    lines.append("")
    cur_topic = topic_data.get("current", {})
    if cur_topic.get("topic"):
        lines.append(f"## Round Topic")
        lines.append(f"**Current (cycle {src}):** {cur_topic['topic']}")
        lines.append(cur_topic.get("description", "")[:200])
        lines.append("")
    queue = topic_data.get("queue", [])
    if queue:
        lines.append("**Queued for next:** " + "; ".join(
            q if isinstance(q, str) else q.get("topic", "?") for q in queue[:3]))
        lines.append("")
    else:
        lines.append("*No items in round_topic.json queue - propose new topic below.*")
        lines.append("")

    lines.append("## Proposed Goals (stubs - refine before goal-setting)")
    lines.append("")
    for i, s in enumerate(stubs, 1):
        lines.append(f"{i}. **{s['title']}** - *Pillar: {s['pillar']}*")
        lines.append(f"   Rationale: {s['rationale']}")
        lines.append("   Verification: (TBD - define acceptance criteria)")
        lines.append("")

    lines.append(f"## Completion Summary (cycle-{src} inputs)")
    lines.append(f"Total verified goals found: {len(completed)}")
    lines.append("")
    if completed:
        lines.append("### Key completed capabilities (sample):")
        for g in completed[:12]:
            src_file = Path(g["source"]).name
            lines.append(f"- {g['title']} (from {src_file})")
        lines.append("")

    if patterns:
        lines.append("### Decision-log patterns observed:")
        for p in patterns[:5]:
            lines.append(f"- Recurring {p['type']} events ({p['count']}x) across agents: {p['agents']}")
        lines.append("")

    lines.append("---")
    lines.append("*Auto-generated skeleton. Refine each stub with specific acceptance criteria before cycle goal-setting.*")
    return "\n".join(lines), next_cycle, len(stubs)

def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    cycle_num = None
    source_cycle = None
    if "--cycle" in args:
        idx = args.index("--cycle")
        cycle_num = int(args[idx + 1])
    if "--source-cycle" in args:
        idx = args.index("--source-cycle")
        source_cycle = int(args[idx + 1])

    base = Path(__file__).resolve().parent.parent.parent
    goal_dir = base / "memory" / "goals"
    decision_log = base / "memory" / "ops" / "decision-log.jsonl"
    topic_path = base / "memory" / "goals" / "round_topic.json"

    print(f"Generating skeleton for cycle {cycle_num or 'auto'} (from cycle {source_cycle or 'auto'})...")
    skeleton, next_cycle, n_stubs = generate_skeleton(
        goal_dir, decision_log, topic_path,
        cycle_num=cycle_num, source_cycle=source_cycle
    )
    print(skeleton)
    out_path = goal_dir / f"cycle{next_cycle}-skeleton.md"
    if dry_run:
        print(f"[DRY-RUN] Would write to {out_path} ({n_stubs} stubs)")
    else:
        out_path.write_text(skeleton, encoding="utf-8")
        print(f"WROTE: {out_path} ({n_stubs} stubs)")

if __name__ == "__main__":
    main()
