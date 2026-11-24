"""seat_router.py - Re-route open goals from unreachable seats to nearest available agent.

Triggered at run start: checks if each seat is reachable (last response < 30min).
If unreachable, re-routes its open goals to the first available fallback from seat-routing-map.json.
Logs re-routes to decision-log.jsonl.

Usage: python memory/orchestrator/seat_router.py [--verbose]
"""
import pathlib, json, datetime, sys

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
ROUTING_MAP = BASE / "memory" / "ops" / "seat-routing-map.json"
NEXT10 = BASE / "memory" / "goals" / "next10.json"
DECISION_LOG = BASE / "memory" / "ops" / "decision-log.jsonl"
AUTOLOOP = BASE / "memory" / "ops" / "autoloop.jsonl"
STALE_THRESHOLD_MIN = 30

def check_availability():
    """Check which agents are reachable based on last activity in autoloop.jsonl."""
    availability = {}
    if not AUTOLOOP.exists():
        # No data - assume all available
        return {name: True for name in ["orchestrator","researcher","builder","verifier","designer","archivist","scribe","mechanic"]}
    
    lines = AUTOLOOP.read_text(encoding="utf-8").strip().splitlines()
    last_seen = {}
    for line in lines[-200:]:  # check last 200 entries
        try:
            entry = json.loads(line)
            agent = entry.get("agent", "").lower()
            ts = entry.get("timestamp", "")
            if agent and ts:
                if agent not in last_seen or ts > last_seen[agent]:
                    last_seen[agent] = ts
        except (json.JSONDecodeError, TypeError):
            continue
    
    now = datetime.datetime.now(datetime.timezone.utc)
    for agent in ["orchestrator","researcher","builder","verifier","designer","archivist","scribe","mechanic"]:
        if agent in last_seen:
            try:
                last_ts = datetime.datetime.fromisoformat(last_seen[agent].replace('Z', '+00:00'))
                age_min = (now - last_ts).total_seconds() / 60
                availability[agent] = age_min < STALE_THRESHOLD_MIN
            except (ValueError, AttributeError):
                availability[agent] = True  # can't parse - assume available
        else:
            availability[agent] = True  # no data - assume available
    
    return availability

def get_open_goals_by_agent():
    """Get open goals per agent from next10.json."""
    if not NEXT10.exists():
        return {}
    data = json.loads(NEXT10.read_text(encoding="utf-8"))
    goals = {}
    for g in data.get("next10", []):
        agent = g.get("agent", "unknown").lower()
        if agent not in goals:
            goals[agent] = []
        goals[agent].append(g)
    return goals

def route_goals(unreachable_agents, availability):
    """Re-route goals from unreachable agents to available fallbacks."""
    if not ROUTING_MAP.exists():
        print("[seat_router] No routing map found")
        return []
    
    routes = json.loads(ROUTING_MAP.read_text(encoding="utf-8"))
    goals_by_agent = get_open_goals_by_agent()
    reroutes = []
    
    for agent in unreachable_agents:
        if availability.get(agent, True):
            continue  # actually available
        fallbacks = routes["routes"].get(agent, {}).get("fallbacks", [])
        agent_goals = goals_by_agent.get(agent, [])
        
        for fb in fallbacks:
            if availability.get(fb, False):
                for goal in agent_goals:
                    reroutes.append({
                        "from": agent,
                        "to": fb,
                        "goal_title": goal.get("title", "")[:80],
                        "reason": f"{agent} unreachable (stale >{STALE_THRESHOLD_MIN}min)"
                    })
                break  # only route to first available fallback
    
    return reroutes

def main():
    verbose = "--verbose" in sys.argv
    # Support --unreachable <agent> for testing/forced re-route
    forced_unreachable = set()
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == '--unreachable' and i + 1 < len(args):
            forced_unreachable.add(args[i+1])
    
    availability = check_availability()
    # Override with forced unreachable
    for agent in forced_unreachable:
        availability[agent] = False
    
    if verbose:
        print("[seat_router] Availability:")
        for agent, avail in sorted(availability.items()):
            status = "OK" if avail else "STALE"
            print(f"  {agent}: {status}")
    
    unreachable = [a for a, v in availability.items() if not v]
    
    if not unreachable:
        print("[seat_router] All seats reachable - no re-routing needed")
        return 0
    
    reroutes = route_goals(unreachable, availability)
    
    if reroutes:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        log_entry = {
            "timestamp": now_iso,
            "type": "seat_reroute",
            "unreachable": unreachable,
            "reroutes": reroutes,
            "detail": f"Re-routed {len(reroutes)} goals from {len(unreachable)} unreachable seats"
        }
        with open(DECISION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        print(f"[seat_router] Re-routed {len(reroutes)} goals:")
        for r in reroutes[:5]:
            print(f"  {r['from']} -> {r['to']}: {r['goal_title']}")
    else:
        print("[seat_router] Unreachable seats have no open goals to re-route")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
