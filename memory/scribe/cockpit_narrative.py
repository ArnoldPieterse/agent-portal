#!/usr/bin/env python3
"""Cockpit Narrative Layer - produces a 2-3 sentence fleet status narrative.

Usage: python memory/scribe/cockpit_narrative.py [--json]
Output: Natural-language summary suitable for the cockpit tab header.
Accepts optional --data <path> to use a pre-built cockpit JSON instead of auto-collecting.
"""
import json, re, os, sys, time
from datetime import datetime

KNOWN_AGENTS = ["orchestrator", "researcher", "builder", "verifier", "designer", "mechanic", "scribe"]

def load_agents():
    """Load agent roster from agents.json."""
    try:
        with open("agents.json") as f:
            data = json.load(f)
        return data.get("agents", [])
    except Exception:
        return []

def count_goals(agent_dir="memory/goals"):
    """Count reached vs open goals per known agent from goal files."""
    results = {}
    if not os.path.isdir(agent_dir):
        return results
    for agent in KNOWN_AGENTS:
        path = os.path.join(agent_dir, f"{agent}.md")
        if not os.path.exists(path):
            continue
        try:
            with open(path) as f:
                content = f.read()
        except Exception:
            continue
        # Goals are numbered lines like "1. **Title**"
        total = len(re.findall(r"^\d+\. \*\*", content, re.MULTILINE))
        verified = len(re.findall(r"\(verified:", content))
        reached = min(verified, total)
        open_count = max(0, total - reached)
        results[agent] = {"total": total, "reached": reached, "open": open_count}
    return results

def get_health_score(goal_stats):
    """Compute a 0-100 health score from goal completion + roster presence."""
    if not goal_stats:
        return 50
    total_goals = sum(v["total"] for v in goal_stats.values())
    reached_goals = sum(v["reached"] for v in goal_stats.values())
    if total_goals == 0:
        return 50
    completion_pct = (reached_goals / total_goals) * 100
    roster_score = (len(goal_stats) / len(KNOWN_AGENTS)) * 100
    score = completion_pct * 0.6 + roster_score * 0.4
    return max(0, min(100, round(score)))

def detect_risks(goal_stats):
    """Identify top risks from available data (max 3)."""
    risks = []
    # Check for open blockers
    blockers_path = "memory/ops/blockers.md"
    if os.path.exists(blockers_path):
        with open(blockers_path) as f:
            bcontent = f.read()
        active_blockers = len(re.findall(r"^### ", bcontent, re.MULTILINE))
        if active_blockers > 0:
            risks.append(f"{active_blockers} active blocker(s) in ops log")
    # Check for agents with 0 progress (stalled) - only real agents
    stalled = [a for a, s in goal_stats.items() if s["total"] > 0 and s["reached"] == 0]
    if stalled:
        risks.append(f"{len(stalled)} agent(s) at 0% completion ({', '.join(sorted(stalled)[:3])})")
    # Check model load status from MEMORY.md
    mem_path = "MEMORY.md"
    if os.path.exists(mem_path):
        with open(mem_path) as f:
            mem = f.read()
        if "not_loaded" in mem or "unreachable" in mem.lower():
            risks.append("Some seats not loaded/reachable")
    return risks[:3]

def generate_narrative(cockpit_data=None):
    """Generate 2-3 sentence fleet narrative from raw data.
    
    Args:
        cockpit_data: optional dict with keys: health_score, agents, goals, risks
                      If None, auto-collects from local files.
    Returns:
        dict with 'narrative' (str), 'health_score' (int 0-100), metadata
    """
    start = time.time()
    
    if cockpit_data is None:
        agents = load_agents()
        goal_stats = count_goals()
        score = get_health_score(goal_stats)
        risks = detect_risks(goal_stats)
    else:
        agents = cockpit_data.get("agents", load_agents())
        goal_stats = cockpit_data.get("goals", count_goals())
        score = cockpit_data.get("health_score", get_health_score(goal_stats))
        risks = cockpit_data.get("risks", detect_risks(goal_stats))
    
    # Sentence 1: Overall status
    if score >= 70:
        s1 = f"Fleet healthy (score {score})."
    elif score >= 40:
        s1 = f"Fleet operational with gaps (score {score})."
    else:
        s1 = f"Fleet degraded (score {score}) - attention needed."
    
    # Sentence 2: Goal progress summary
    total_reached = sum(v["reached"] for v in goal_stats.values())
    total_all = sum(v["total"] for v in goal_stats.values())
    if total_all > 0:
        pct = round(total_reached / total_all * 100)
        s2 = f"{total_reached}/{total_all} goals reached fleet-wide ({pct}%)."
    else:
        s2 = "No goals tracked yet this cycle."
    
    # Sentence 3: Risks or all-clear
    if risks:
        top_risk = risks[0]
        s3 = f"Watch item: {top_risk}."
    else:
        s3 = "No active incidents in last 24h."
    
    narrative = f"{s1} {s2} {s3}"
    elapsed = time.time() - start
    
    return {
        "narrative": narrative,
        "health_score": score,
        "goals_reached": total_reached,
        "goals_total": total_all,
        "risks": risks,
        "generation_time_s": round(elapsed, 3),
        "timestamp": datetime.now().isoformat()
    }

def main():
    output = generate_narrative()
    
    if "--json" in sys.argv:
        print(json.dumps(output, indent=2))
    else:
        print(output["narrative"])
        print(f"\n[score={output['health_score']}, goals={output['goals_reached']}/{output['goals_total']}, gen={output['generation_time_s']}s]")
    
    # Write to a stable location for the cockpit UI to read
    out_path = "memory/scribe/cockpit_narrative_latest.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
