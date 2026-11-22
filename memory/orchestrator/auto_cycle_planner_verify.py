#!/usr/bin/env python3
"""Verification of auto_cycle_planner.py on cycle-9 data.

Criteria:
1. Planner allocation predicts >=70% of actual cycle-9 completions
2. No agent assigned 0 or >15 goals
3. Output is valid markdown matching TODO.md format
"""
import re, json, sys, os
sys.path.insert(0, "memory/orchestrator")
from auto_cycle_planner import (
    parse_goal_files, compute_throughput, classify_goal,
    score_assignment, allocate_goals, render_allocation
)

def extract_cycle9_backlog():
    """Extract all goals from cycle-9 archived files as the backlog."""
    archive = "memory/goals/archive"
    pattern = re.compile(r"^\d+\. \*\*(.+?)\*\*")
    backlog = []
    for fname in sorted(os.listdir(archive)):
        if not fname.endswith("-cycle9.md"):
            continue
        agent = fname.split("-")[0]
        path = os.path.join(archive, fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        for line in content.split("\n"):
            m = pattern.match(line.strip())
            if m:
                title = m.group(1).strip()
                backlog.append({"title": title, "description": line, "tags": []})
    return backlog

def main():
    print("=" * 60)
    print("AUTO CYCLE PLANNER - VERIFICATION ON CYCLE-9 DATA")
    print("=" * 60)
    
    # Step 1: Get historical throughput from pre-cycle-9 data
    history = parse_goal_files(cycles=8)
    throughput = compute_throughput(history)
    print("\n[1] Historical throughput (cycles 1-8):")
    for agent, stats in sorted(throughput.items()):
        print(f"    {agent:12s} completed={stats['completed']:3d} "
              f"total={stats['total']:3d} rate={stats['completion_rate']:.0%}")
    
    # Step 2: Extract cycle-9 backlog (what was actually assigned)
    backlog = extract_cycle9_backlog()
    print(f"\n[2] Cycle-9 backlog extracted: {len(backlog)} goals")
    
    if len(backlog) == 0:
        print("FATAL: No cycle-9 goals found in archive")
        sys.exit(1)
    
    # Step 3: Run the planner
    capacity = {"hosts": [], "agents": list(throughput.keys())}
    allocation = allocate_goals(backlog, throughput, capacity)
    
    # Step 4: Check constraint - no agent gets 0 or >15 goals
    print("\n[3] Allocation per agent:")
    constraints_ok = True
    for agent in sorted(set(list(allocation.keys()) + list(throughput.keys()))):
        count = len(allocation.get(agent, []))
        flag = "OK" if 0 < count <= 15 else "FAIL"
        if count == 0 or count > 15:
            constraints_ok = False
        print(f"    {agent:12s} {count:3d} goals [{flag}]")
    
    # Step 5: Compare planner allocation vs actual cycle-9 assignment
    print("\n[4] Prediction accuracy (planner vs actual):")
    archive = "memory/goals/archive"
    pattern = re.compile(r"^\d+\. \*\*(.+?)\*\*")
    actual_by_agent = {}
    for fname in sorted(os.listdir(archive)):
        if not fname.endswith("-cycle9.md"):
            continue
        agent = fname.split("-")[0]
        with open(os.path.join(archive, fname), "r", encoding="utf-8") as f:
            content = f.read()
        goals = []
        for line in content.split("\n"):
            m = pattern.match(line.strip())
            if m:
                goals.append(m.group(1).strip().lower())
        actual_by_agent[agent] = goals
    
    total_actual = sum(len(v) for v in actual_by_agent.values())
    correct = 0
    for agent, planned_titles in allocation.items():
        actual_titles = set(actual_by_agent.get(agent, []))
        for gt in planned_titles:
            if gt.lower() in actual_titles:
                correct += 1
    
    accuracy = correct / total_actual if total_actual > 0 else 0
    print(f"    Total actual goals: {total_actual}")
    print(f"    Correctly predicted (right agent): {correct}")
    print(f"    Accuracy: {accuracy:.0%} (target: >=70%)")
    
    # Step 6: Validate markdown output
    md = render_allocation(allocation, "CYCLE-10-TEST", "Test topic")
    has_header = "# CYCLE-10-TEST" in md
    has_agents = all(a in md for a in ["Orchestrator", "Builder"])
    has_goals = "**1." in md and "**2." in md
    print(f"\n[5] Markdown validation:")
    print(f"    Has cycle header: {has_header}")
    print(f"    Has agent sections: {has_agents}")
    print(f"    Has numbered goals: {has_goals}")
    
    # Final verdict
    print("\n" + "=" * 60)
    all_pass = (accuracy >= 0.70) and constraints_ok and has_header and has_agents and has_goals
    if all_pass:
        print("RESULT: ALL CRITERIA PASSED")
    else:
        reasons = []
        if accuracy < 0.70: reasons.append(f"accuracy {accuracy:.0%} < 70%")
        if not constraints_ok: reasons.append("agent constraint violated")
        if not (has_header and has_agents and has_goals): reasons.append("markdown format incomplete")
        print(f"RESULT: FAILED - {'; '.join(reasons)}")
    print("=" * 60)
    
    # Save evidence
    evidence = {
        "test": "auto_cycle_planner_verify",
        "date": "2026-11-23",
        "backlog_size": len(backlog),
        "total_actual_goals": total_actual,
        "correctly_predicted": correct,
        "accuracy_pct": round(accuracy * 100, 1),
        "constraints_ok": constraints_ok,
        "markdown_valid": has_header and has_agents and has_goals,
        "all_pass": all_pass,
    }
    with open("memory/orchestrator/auto_cycle_planner_verify.json", "w") as f:
        json.dump(evidence, f, indent=2)
    print(f"\nEvidence saved to memory/orchestrator/auto_cycle_planner_verify.json")
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
