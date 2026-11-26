"""goal_synth.py - Autonomous Goal-Set Synthesizer (Scribe Cycle 26, Goal #1)

At each GOAL_RESET_PENDING, auto-drafts the next cycle's per-lane goal proposals
from available data sources. Emits one draft file per active lane to
memory/goals/drafts/<lane>.md for Orchestrator ratification.

Data sources (all optional - script degrades gracefully):
  - memory/scribe/intervention-patterns.jsonl  (intervention classes per agent)
  - memory/scribe/autonomy-dependency-graph.json (SPOF nodes, upstream deps)
  - memory/scribe/intervention-cost.jsonl      (cost lines per intervention class)
  - memory/scribe/next-elimination.md          (recommended next eliminations)
  - goal_ledger.json                           (active lanes, open goals)
  - memory/goals/closed_topics.json            (anti-repeat check)

Verification:
  - Runs clean on real data
  - Produces one draft per active lane
  - Every proposed goal cites its data source
  - Built-in check: 0 collisions with closed_topics.json
"""
import pathlib, json, hashlib, re, sys
from datetime import datetime, timezone

ROOT = pathlib.Path(".")


def load_jsonl(path):
    p = ROOT / path
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    results = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return results


def load_json(path):
    p = ROOT / path
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def get_active_lanes():
    """Get lanes with open goals from goal_ledger.json."""
    ledger = load_json("goal_ledger.json")
    if not ledger:
        return []
    active = []
    for agent, info in ledger.get("agents", {}).items():
        if info.get("open", 0) > 0:
            active.append(agent)
    return sorted(active)


def get_open_goal_signatures(lane):
    """Get signatures of currently open goals for a lane."""
    ledger = load_json("goal_ledger.json")
    if not ledger:
        return set()
    sigs = set()
    for g in ledger.get("agents", {}).get(lane, {}).get("goals", []):
        if g.get("status") == "open":
            text = g.get("text", "")
            sig = hashlib.md5(text[:80].lower().encode()).hexdigest()[:12]
            sigs.add(sig)
    return sigs


def get_closed_topic_signatures():
    """Get all closed topic signatures for anti-repeat check."""
    topics = load_json("memory/goals/closed_topics.json")
    if not topics:
        return set(), []
    sigs = set()
    texts = []
    for t in topics:
        sig = t.get("sig", "")
        text = t.get("text", "")
        if sig:
            sigs.add(sig)
        texts.append(text)
    return sigs, texts


def check_collision(goal_text, closed_texts):
    """Check if a proposed goal collides with any closed topic."""
    m = re.match(r"\*\*(.+?)\*\*", goal_text)
    title = m.group(1).lower().strip() if m else goal_text[:40].lower().strip()
    for ct in closed_texts:
        if title in ct.lower():
            return True
        ct_title_m = re.match(r"\*\*(.+?)\*\*", ct)
        if ct_title_m and ct_title_m.group(1).lower().strip()[:20] in title:
            return True
    return False


def generate_goals_for_lane(lane, interventions, dep_graph, cost_lines, next_elim):
    """Generate goal proposals for a lane based on available data."""
    goals = []

    # Source 1: Intervention patterns for this agent
    lane_interventions = [i for i in interventions if i.get("agent", "").lower() == lane.lower()]
    if lane_interventions:
        patterns = {}
        for iv in lane_interventions:
            p = iv.get("pattern", "unknown")
            if p not in patterns:
                patterns[p] = []
            patterns[p].append(iv)

        for pattern, items in sorted(patterns.items()):
            latest = max(items, key=lambda x: x.get("ts", ""))
            goal_text = (
                f"**{pattern.replace('_',' ').title()} Automation for {lane}** - "
                f"Automate the '{pattern}' intervention class for {lane} to eliminate "
                f"manual touchpoints. Based on {len(items)} observed instance(s), "
                f"latest: cycle {latest.get('cycle','?')}. "
                f"`python memory/{lane}/{pattern}_automation.py`: detect the pattern, "
                f"apply the standard resolution, log to intervention-patterns.jsonl. "
                f"Verified: runs clean; eliminates >=80% of '{pattern}' interventions for {lane} "
                f"in a 3-cycle window; no regression in autonomy score. "
                f"[source: intervention-patterns.jsonl, pattern='{pattern}', n={len(items)}]"
            )
            goals.append(goal_text)

    # Source 2: Dependency graph SPOF nodes affecting this lane
    if dep_graph:
        spofs = dep_graph.get("spof_nodes", [])
        for node in spofs:
            affected = node.get("downstream", [])
            if lane.lower() in [a.lower() for a in affected]:
                goal_text = (
                    f"**SPOF Mitigation: {node.get('id','?')}** - "
                    f"Reduce single-point-of-failure risk from '{node.get('id','?')}' "
                    f"(affects {', '.join(affected)}). Add redundancy or auto-recovery. "
                    f"Verified: SPOF node no longer appears in dependency graph as critical; "
                    f"failover test passes. [source: autonomy-dependency-graph.json, node='{node.get('id','?')}']"
                )
                goals.append(goal_text)

    # Source 3: Intervention cost lines (highest-cost first)
    if cost_lines:
        lane_costs = [c for c in cost_lines if c.get("agent", "").lower() == lane.lower()]
        if lane_costs:
            top = max(lane_costs, key=lambda x: x.get("cost_min", 0))
            goal_text = (
                f"**Cost Reduction: {top.get('class','?')}** - "
                f"Reduce intervention cost for '{top.get('class','?')}' class "
                f"(currently {top.get('cost_min',0)} min/instance). "
                f"Target: <=50% reduction via automation. "
                f"Verified: 3-cycle average cost drops >=50% from baseline; no quality regression. "
                f"[source: intervention-cost.jsonl, class='{top.get('class','?')}', cost={top.get('cost_min',0)}min]"
            )
            goals.append(goal_text)

    # Source 4: Next-elimination recommendations
    if next_elim and lane.lower() in next_elim.lower():
        lines = next_elim.split("\n")
        in_section = False
        section_lines = []
        for line in lines:
            if lane.lower() in line.lower() and ("##" in line or "**" in line):
                in_section = True
                continue
            if in_section:
                if line.startswith("## ") or (line.startswith("**") and lane.lower() not in line.lower()):
                    break
                section_lines.append(line)
        if section_lines:
            rec = " ".join(l.strip() for l in section_lines if l.strip())[:200]
            goal_text = (
                f"**Next Elimination: {lane}** - "
                f"Execute the recommended next elimination for {lane}: {rec}. "
                f"Verified: intervention class eliminated; 0 occurrences in next cycle. "
                f"[source: next-elimination.md, lane='{lane}']"
            )
            goals.append(goal_text)

    # Fallback: generic convergence maintenance goal
    if not goals:
        goal_text = (
            f"**{lane.title()} Convergence Maintenance** - "
            f"Maintain {lane}'s convergence trajectory: verify all open goals remain on track, "
            f"check for new intervention patterns, and update evidence. "
            f"`python memory/{lane}/convergence_check.py`: run health check, log results. "
            f"Verified: runs clean; reports status for all open goals; flags any at-risk items. "
            f"[source: goal_ledger.json, lane='{lane}', open_goals={len(get_open_goal_signatures(lane))}]"
        )
        goals.append(goal_text)

    return goals


def main():
    now = datetime.now(timezone.utc).isoformat()

    # Load data sources
    interventions = load_jsonl("memory/scribe/intervention-patterns.jsonl")
    dep_graph = load_json("memory/scribe/autonomy-dependency-graph.json")
    cost_lines = load_jsonl("memory/scribe/intervention-cost.jsonl")
    next_elim_path = ROOT / "memory/scribe/next-elimination.md"
    next_elim = next_elim_path.read_text(encoding="utf-8") if next_elim_path.exists() else None

    # Get active lanes
    active_lanes = get_active_lanes()
    if not active_lanes:
        print("ERROR: No active lanes found in goal_ledger.json")
        return 1

    # Get closed topics for anti-repeat check
    closed_sigs, closed_texts = get_closed_topic_signatures()

    # Ensure drafts directory exists
    drafts_dir = ROOT / "memory" / "goals" / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    results = []
    collisions = 0

    for lane in active_lanes:
        goals = generate_goals_for_lane(lane, interventions, dep_graph, cost_lines, next_elim)

        # Anti-repeat check
        filtered_goals = []
        for g in goals:
            if not check_collision(g, closed_texts):
                filtered_goals.append(g)
            else:
                collisions += 1

        # Write draft file
        draft_path = drafts_dir / f"{lane}.md"
        content_lines = [
            f"# {lane.title()} - Draft Goals (auto-generated by goal_synth.py)",
            f"Generated: {now}",
            f"Data sources: intervention-patterns.jsonl ({len(interventions)} entries), "
            f"dependency-graph ({'yes' if dep_graph else 'no'}), "
            f"intervention-cost ({len(cost_lines) if cost_lines else 0} entries), "
            f"next-elimination ({'yes' if next_elim else 'no'})",
            "",
        ]
        for i, g in enumerate(filtered_goals, 1):
            content_lines.append(f"{i}. {g}")
            content_lines.append("")

        draft_path.write_text("\n".join(content_lines), encoding="utf-8")
        results.append({
            "lane": lane,
            "goals_proposed": len(filtered_goals),
            "draft_path": str(draft_path)
        })
        print(f"  {lane}: {len(filtered_goals)} goal(s) drafted -> {draft_path}")

    # Final report
    total_goals = sum(r["goals_proposed"] for r in results)
    print(f"\nSUMMARY: {len(active_lanes)} lanes, {total_goals} goals drafted, "
          f"{collisions} collision(s) filtered")

    if collisions > 0:
        print(f"WARNING: {collisions} proposed goal(s) collided with closed topics and were excluded.")

    # Write run log
    log_path = ROOT / "memory" / "scribe" / "goal-synth-log.jsonl"
    log_entry = {
        "ts": now,
        "lanes": active_lanes,
        "total_goals": total_goals,
        "collisions": collisions,
        "sources_used": {
            "intervention_patterns": len(interventions),
            "dependency_graph": bool(dep_graph),
            "intervention_cost": len(cost_lines) if cost_lines else 0,
            "next_elimination": bool(next_elim)
        }
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"Log appended to {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
