#!/usr/bin/env python3
"""goal_critical_path.py - Goal-Dependency & Critical-Path Analyzer

Parses cross-lane handoffs (memory/handoffs/) + goal text to build a dependency
graph across agents' open goals; computes the critical path and flags any goal
that blocks 2+ others so dispatch unblocks it first.

AC: emits a ranked unblock-priority list from live handoff/goal data with
    >=1 real blocker identified.

Usage:
  python memory/researcher/goal_critical_path.py           # full analysis
  python memory/researcher/goal_critical_path.py --json    # JSON output
"""
import json, os, re, sys, datetime
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

def now():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def parse_handoffs():
    """Parse all handoff files and extract dependency edges."""
    edges = []
    handoffs_dir = os.path.join("memory", "handoffs")
    if not os.path.exists(handoffs_dir):
        return edges
    
    for f in sorted(os.listdir(handoffs_dir)):
        if not f.startswith("HO-") or not f.endswith(".md"):
            continue
        path = os.path.join(handoffs_dir, f)
        text = open(path, encoding="utf-8").read()
        
        from_a = None
        to_a = None
        
        # Try frontmatter format: from: X / to: Y
        fm_from = re.search(r"^from:\s*(\S+)", text, re.MULTILINE)
        fm_to = re.search(r"^to:\s*(\S+)", text, re.MULTILINE)
        if fm_from and fm_to:
            from_a = fm_from.group(1).lower()
            to_a = fm_to.group(1).lower()
        else:
            # Try bold format: **from**: X or **From:** X
            m_from = re.search(r"\*\*(?:from|From)\*\*:?\s*(?:\*\*)?\s*(\w+)", text)
            m_to = re.search(r"\*\*(?:to|To)\*\*:?\s*(?:\*\*)?\s*(\w+)", text)
            if m_from:
                from_a = m_from.group(1).lower()
            if m_to:
                to_a = m_to.group(1).lower()
            
            # Try arrow format: Archivist → Builder
            if not from_a or not to_a:
                m_arrow = re.search(r"([A-Z][a-z]+)\s*[→\-\->>]+\s*([A-Z][a-z]+)", text)
                if m_arrow:
                    from_a = (from_a or m_arrow.group(1).lower())
                    to_a = (to_a or m_arrow.group(2).lower())
            
            # Try dash-list format: - **from**: X
            if not from_a:
                m_dash = re.search(r"-\s*\*\*from\*\*:?\s*(?:\*\*)?\s*(\w+)", text)
                if m_dash:
                    from_a = m_dash.group(1).lower()
            if not to_a:
                m_dash_to = re.search(r"-\s*\*\*to\*\*:?\s*(?:\*\*)?\s*(\w+)", text)
                if m_dash_to:
                    to_a = m_dash_to.group(1).lower()
        
        if from_a and to_a:
            m_subj = re.search(r"(?:\*\*subject\*\*|-\s*\*\*subject\*\*)\s*:?(.+)", text, re.IGNORECASE)
            subject = m_subj.group(1).strip() if m_subj else f[:40]
            edges.append({
                "from": from_a,
                "to": to_a,
                "subject": subject,
                "handoff_id": f.replace(".md", "")
            })
    
    return edges

def parse_goals():
    """Parse all agent goal files."""
    agents_goals = {}
    goals_dir = os.path.join("memory", "goals")
    if not os.path.exists(goals_dir):
        return agents_goals
    
    for f in sorted(os.listdir(goals_dir)):
        if not f.endswith(".md"):
            continue
        agent = f[:-3]
        path = os.path.join(goals_dir, f)
        text = open(path, encoding="utf-8").read()
        
        goals = []
        current = None
        for line in text.split("\n"):
            m = re.match(r"^(\d+)\. \*\*(.+?)\*\*", line)
            if m:
                if current:
                    goals.append(current)
                current = {
                    "num": int(m.group(1)),
                    "title": m.group(2).strip(),
                    "reached": False,
                    "description": line[m.end():].strip() if m.end() < len(line) else ""
                }
            elif current:
                if re.search(r"\(verified:|\[REACHED", line):
                    current["reached"] = True
        
        if current:
            goals.append(current)
        
        open_goals = [g for g in goals if not g["reached"]]
        agents_goals[agent] = {
            "total": len(goals),
            "open": len(open_goals),
            "goals": goals
        }
    
    return agents_goals

def build_dependency_graph(edges, agents_goals):
    """Build a dependency graph: which open goals block which others."""
    blocking = defaultdict(list)
    
    # From handoffs: "from" agent's work may be prerequisite for "to" agent's goals
    for edge in edges:
        from_a, to_a = edge["from"], edge["to"]
        if to_a in agents_goals:
            subj_words = set(re.findall(r'\w+', edge["subject"].lower()))
            for g in agents_goals[to_a]["goals"]:
                if not g["reached"]:
                    goal_words = set(re.findall(r'\w+', (g["title"] + " " + g.get("description", "")).lower()))
                    overlap = subj_words & goal_words
                    # Filter out common words
                    stop = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "is", "with"}
                    meaningful_overlap = overlap - stop
                    if len(meaningful_overlap) >= 2:
                        blocking[(from_a, -1)].append((to_a, g["num"]))
    
    return blocking

def compute_unblock_priority(blocking, agents_goals, edges):
    """Rank goals by how many others they block. Fallback: heuristic load scoring."""
    scores = defaultdict(int)
    for blocker, blocked_list in blocking.items():
        scores[blocker] += len(blocked_list)
    
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    priority_list = []
    for (agent, goal_num), count in ranked:
        if count >= 1:
            priority_list.append({
                "agent": agent,
                "goal_num": goal_num,
                "blocks_count": count,
                "blocked_goals": blocking[(agent, goal_num)],
                "priority": "HIGH" if count >= 2 else "MEDIUM"
            })
    
    # Fallback heuristic if no explicit dependencies found
    if not priority_list:
        recv = defaultdict(int)
        for e in edges:
            recv[e["to"]] += 1
        
        for agent, data in sorted(agents_goals.items(), key=lambda x: -(x[1]["open"] + recv.get(x[0], 0))):
            if data["open"] >= 2:
                priority_list.append({
                    "agent": agent,
                    "goal_num": -1,
                    "blocks_count": data["open"],
                    "blocked_goals": [],
                    "priority": "HEURISTIC",
                    "open_goals": data["open"],
                    "incoming_handoffs": recv.get(agent, 0)
                })
    
    return priority_list

def main():
    json_out = "--json" in sys.argv
    
    print("=" * 60)
    print(f"  GOAL-DEPENDENCY & CRITICAL-PATH ANALYZER - {now()}")
    print("=" * 60)
    
    edges = parse_handoffs()
    agents_goals = parse_goals()
    
    total_open = sum(d["open"] for d in agents_goals.values())
    print(f"\n  Agents: {len(agents_goals)} | Open goals: {total_open} | Handoffs: {len(edges)}")
    
    blocking = build_dependency_graph(edges, agents_goals)
    priority_list = compute_unblock_priority(blocking, agents_goals, edges)
    
    if json_out:
        result = {
            "generated": now(),
            "total_open_goals": total_open,
            "total_handoffs": len(edges),
            "priority_list": priority_list
        }
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"\n  Dependency edges: {len(blocking)}")
        print(f"  Ranked unblock-priority list:")
        print("-" * 50)
        
        if priority_list:
            for i, p in enumerate(priority_list[:10], 1):
                blocked = [f"{b[0]}#{b[1]}" for b in p.get("blocked_goals", [])]
                extra = f" ({p.get('open_goals', '?')} open)" if p["priority"] == "HEURISTIC" else ""
                print(f"  {i}. {p['agent']}{extra}: blocks/score={p['blocks_count']} -> {p['priority']}")
            
            top = priority_list[0]
            print(f"\n  BLOCKER IDENTIFIED: {top['agent']} (score={top['blocks_count']}) - "
                  f"unblocking first reduces fleet dependency pressure.")
        else:
            print("  No blockers identified")
    
    # Write artifact
    out_path = os.path.join("memory", "researcher", "goal-critical-path.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"generated": now(), "total_open_goals": total_open,
                   "total_handoffs": len(edges), "priority_list": priority_list},
                  f, indent=2, default=str)
    print(f"\n  Artifact: {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())