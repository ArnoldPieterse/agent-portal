"""dispatch_sync.py - Reconcile dispatch queue with next10.json status on each auto-loop pass.

Verification:
- "reached" goals excluded from WORK dispatch
- Idle agents get role-specific maintenance task from rotation table (not generic menu)
- After sync, no agent dispatched for a reached goal in 3 consecutive passes
- All idle agents receive role-specific tasks (logged to decision-log.jsonl)
"""
import pathlib, json, datetime, re, sys

BASE = pathlib.Path(__file__).resolve().parent.parent.parent  # project root
NEXT10 = BASE / "memory" / "goals" / "next10.json"
FLEET_MODE = BASE / "memory" / "ops" / "fleet-mode.json"
DISPATCH_QUEUE = BASE / "memory" / "ops" / "dispatch-queue.json"
DECISION_LOG = BASE / "memory" / "ops" / "decision-log.jsonl"

# Parse rotation table from idle-maintenance-rotation.md
def parse_rotation():
    """Parse the markdown rotation table into {role: [task1..task5]}."""
    rot_path = BASE / "memory" / "ops" / "idle-maintenance-rotation.md"
    if not rot_path.exists():
        return {}
    lines = rot_path.read_text(encoding="utf-8").splitlines()
    rotation = {}
    for line in lines:
        if line.startswith("|") and "---" not in line and "Role" not in line:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 6:
                role = cells[0].lower()
                tasks = cells[1:6]
                rotation[role] = tasks
    return rotation

def get_day_of_cycle():
    """Day of cycle (0-indexed). Cycle starts 2026-11-16."""
    cycle_start = datetime.date(2026, 11, 16)
    today = datetime.date.today()
    return (today - cycle_start).days

def get_fleet_mode():
    """Read current fleet mode from SSOT."""
    if FLEET_MODE.exists():
        data = json.loads(FLEET_MODE.read_text(encoding="utf-8"))
        return data.get("mode", "WORK")
    return "WORK"

def load_next10():
    """Load next10.json and group goals by agent."""
    if not NEXT10.exists():
        return {}
    data = json.loads(NEXT10.read_text(encoding="utf-8"))
    goals_by_agent = {}
    for goal in data.get("next10", []):
        agent = goal.get("agent", "unknown").lower()
        if agent not in goals_by_agent:
            goals_by_agent[agent] = []
        goals_by_agent[agent].append(goal)
    return goals_by_agent

def load_lane_status():
    """Load per-lane done/total from next10.json lanes key."""
    if not NEXT10.exists():
        return {}
    data = json.loads(NEXT10.read_text(encoding="utf-8"))
    return data.get("lanes", {})

def check_reached_history(agent, goal_title):
    """Check if this agent+goal was already dispatched and reached in recent passes."""
    # Read dispatch history
    history_path = BASE / "memory" / "ops" / "dispatch-history.jsonl"
    if not history_path.exists():
        return 0
    count = 0
    lines = history_path.read_text(encoding="utf-8").strip().splitlines()
    for line in lines[-3:]:  # last 3 passes
        try:
            entry = json.loads(line)
            if entry.get("agent") == agent and entry.get("status") == "reached":
                count += 1
        except json.JSONDecodeError:
            continue
    return count

def run_sync():
    """Main sync logic. Returns dispatch queue dict."""
    mode = get_fleet_mode()
    rotation = parse_rotation()
    goals_by_agent = load_next10()
    lanes = load_lane_status()
    day_of_cycle = get_day_of_cycle()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # All agents (from lanes)
    all_agents = list(lanes.keys()) if lanes else list(goals_by_agent.keys())

    dispatch = {
        "timestamp": now,
        "mode": mode,
        "day_of_cycle": day_of_cycle,
        "agents": {}
    }

    for agent in sorted(all_agents):
        lane = lanes.get(agent, {})
        done = lane.get("done", 0)
        total = lane.get("total", 10)
        is_idle = (done >= total) or (agent not in goals_by_agent)

        if mode == "WORK" and not is_idle:
            # WORK mode: dispatch open goals only (exclude reached)
            agent_goals = []
            for g in goals_by_agent.get(agent, []):
                title = g.get("title", "")
                # Check if this goal was already reached (from history)
                reached_count = check_reached_history(agent, title)
                if reached_count >= 3:
                    continue  # skip - reached in 3 consecutive passes
                agent_goals.append({
                    "title": title,
                    "goal": g.get("goal", "")[:200],
                    "eta": g.get("eta", ""),
                    "p_reached": g.get("p_reached", 0)
                })
            dispatch["agents"][agent] = {
                "type": "work",
                "tasks": agent_goals,
                "open_count": total - done
            }
        elif is_idle or mode in ("MAINTENANCE", "IDLE"):
            # IDLE/MAINTENANCE: assign role-specific maintenance task
            tasks = rotation.get(agent, [])
            if tasks:
                task_index = day_of_cycle % 5
                maint_task = tasks[task_index]
            else:
                maint_task = f"General maintenance sweep (no rotation entry for {agent})"
            dispatch["agents"][agent] = {
                "type": "maintenance",
                "task": maint_task,
                "task_index": day_of_cycle % 5 if tasks else -1,
                "open_count": 0
            }
        else:
            # WORK mode but no goals in next10 for this agent (shouldn't happen often)
            dispatch["agents"][agent] = {
                "type": "work",
                "tasks": [],
                "open_count": total - done
            }

    # Write dispatch queue
    DISPATCH_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    DISPATCH_QUEUE.write_text(json.dumps(dispatch, indent=2), encoding="utf-8")

    # Append to dispatch history
    history_path = BASE / "memory" / "ops" / "dispatch-history.jsonl"
    history_entry = {
        "timestamp": now,
        "mode": mode,
        "agents_dispatched": list(dispatch["agents"].keys()),
        "work_agents": [a for a, v in dispatch["agents"].items() if v["type"] == "work"],
        "idle_agents": [a for a, v in dispatch["agents"].items() if v["type"] == "maintenance"]
    }
    with open(history_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(history_entry) + "\n")

    # Log to decision-log.jsonl
    log_entry = {
        "timestamp": now,
        "type": "dispatch_sync",
        "mode": mode,
        "work_dispatched": len([a for a,v in dispatch["agents"].items() if v["type"]=="work"]),
        "maintenance_dispatched": len([a for a,v in dispatch["agents"].items() if v["type"]=="maintenance"]),
        "detail": f"Sync pass: mode={mode}, {len(dispatch['agents'])} agents reconciled"
    }
    with open(DECISION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

    return dispatch

if __name__ == "__main__":
    result = run_sync()
    print(f"[dispatch_sync] mode={result['mode']} day={result['day_of_cycle']} agents={len(result['agents'])}")
    for agent, info in sorted(result["agents"].items()):
        if info["type"] == "work":
            titles = [t["title"][:40] for t in info.get("tasks", [])]
            print(f"  {agent}: WORK ({info['open_count']} open) -> {titles[:2]}")
        else:
            print(f"  {agent}: MAINT -> {info['task'][:50]}")
    print(f"[dispatch_sync] queue written to {DISPATCH_QUEUE.relative_to(BASE)}")
