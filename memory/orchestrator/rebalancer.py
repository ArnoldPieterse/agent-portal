"""
Workload Rebalancer - Orchestrator goal #4
Detects agent overload (queue depth >3 or p95 response >30s)
and proposes task redistribution to underloaded agents.
Writes decisions to decision-log.jsonl.
"""
import json, time, pathlib, statistics
from dataclasses import dataclass, field
from typing import Optional

DECISION_LOG = pathlib.Path("decision-log.jsonl")

# ── Data model ────────────────────────────────────────────────────────────────
@dataclass
class AgentStats:
    name: str
    queue_depth: int = 0
    p95_response_s: float = 0.0   # seconds
    normal_load: float = 1.0      # baseline (1.0 = 1 agent-equivalent)
    current_assigned: list = field(default_factory=list)  # task IDs

def is_overloaded(a: AgentStats) -> bool:
    return a.queue_depth > 3 or a.p95_response_s > 30.0

def is_underloaded(a: AgentStats, fleet_avg_queue: float) -> bool:
    """An agent is underloaded if its queue is below fleet average and not itself overloaded."""
    return (not is_overloaded(a)) and a.queue_depth < fleet_avg_queue

# ── Core rebalancing logic ───────────────────────────────────────────────────
def compute_rebalance(agents: list[AgentStats]) -> dict:
    """
    Returns a decision dict with proposed redistributions.
    Rules:
      - Only move tasks from overloaded agents to underloaded ones
      - No agent may end up with > 1.5x its normal_load in queue depth
      - Prefer moving the fewest tasks needed to bring each overloaded agent below threshold
    """
    overloaded   = [a for a in agents if is_overloaded(a)]
    fleet_avg_q  = sum(a.queue_depth for a in agents) / max(len(agents), 1)
    underloaded  = [a for a in agents if is_underloaded(a, fleet_avg_q)]

    moves: list[dict] = []
    # working copy of queue depths so we can simulate
    depth = {a.name: a.queue_depth for a in agents}
    normal = {a.name: a.normal_load for a in agents}
    tasks  = {a.name: list(a.current_assigned) for a in agents}

    for src in sorted(overloaded, key=lambda x: -depth[x.name]):
        # target queue depth: bring to <=3 (queue threshold)
        excess = max(0, depth[src.name] - 3)
        if excess == 0:
            continue

        moved = 0
        for dst in sorted(underloaded, key=lambda x: depth[x.name]):
            if moved >= excess:
                break
            # How many can we give to dst without exceeding 1.5x normal load?
            max_dst_queue = int(normal[dst.name] * 1.5)
            capacity = max(0, max_dst_queue - depth[dst.name])
            if capacity == 0:
                continue
            take = min(capacity, excess - moved)
            # pick actual task IDs from src
            moved_tasks = tasks[src.name][len(tasks[src.name])-take : ] if take <= len(tasks[src.name]) else []
            for t in moved_tasks:
                moves.append({"task": t, "from": src.name, "to": dst.name})
            depth[src.name] -= take
            depth[dst.name] += take
            tasks[src.name] = tasks[src.name][:len(tasks[src.name])-take]
            tasks[dst.name].extend(moved_tasks)
            moved += take

    # Build final assignment summary
    final_loads = {a.name: depth[a.name] for a in agents}
    violations  = [n for n, d in final_loads.items() if d > normal[n] * 1.5]

    decision = {
        "source": "rebalancer",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overloaded_agents": [a.name for a in overloaded],
        "underloaded_agents": [a.name for a in underloaded],
        "moves": moves,
        "final_queue_depths": final_loads,
        "load_violations": violations,   # must be empty
        "preconditions_met": len(agents) >= 2 and len(overloaded) > 0,
        "rollback": "revert all 'moves' entries to original assignment",
    }
    return decision

def log_decision(decision: dict):
    DECISION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DECISION_LOG, "a") as f:
        f.write(json.dumps(decision) + "\n")

# ── Self-test / verification harness ─────────────────────────────────────────
def self_test():
    """
    Simulated 2-agent-overload scenario:
      - Alpha: queue=5, p95=35s  (overloaded)
      - Beta:  queue=4, p95=10s  (overloaded on queue depth)
      - Gamma: queue=1, p95=5s   (underloaded)
      - Delta: queue=0, p95=2s   (underloaded)
    Verify:
      a) rebalancer proposes valid redistribution
      b) no agent assigned > 1.5x normal load
      c) decision logged with all required fields
    """
    # normal_load = expected steady-state queue depth (5 tasks is "normal")
    agents = [
        AgentStats(name="Alpha", queue_depth=5, p95_response_s=35.0, normal_load=5,
                   current_assigned=["t1","t2","t3","t4","t5"]),
        AgentStats(name="Beta",  queue_depth=4, p95_response_s=10.0, normal_load=5,
                   current_assigned=["t6","t7","t8","t9"]),
        AgentStats(name="Gamma", queue_depth=1, p95_response_s=5.0,  normal_load=5,
                   current_assigned=["t10"]),
        AgentStats(name="Delta", queue_depth=0, p95_response_s=2.0,  normal_load=5,
                   current_assigned=[]),
    ]

    d = compute_rebalance(agents)

    required_fields = {"source","timestamp","overloaded_agents","underloaded_agents",
                       "moves","final_queue_depths","load_violations",
                       "preconditions_met","rollback"}
    missing = required_fields - set(d.keys())
    assert not missing, f"Missing fields: {missing}"

    # a) valid redistribution proposed
    assert len(d["moves"]) > 0, "No moves proposed in overload scenario"

    # b) no agent exceeds 1.5x normal load
    assert d["load_violations"] == [], f"Load violations: {d['load_violations']}"
    for name, depth in d["final_queue_depths"].items():
        cap = int(5 * 1.5)  # normal_load=5, cap=7
        assert depth <= cap, f"{name} at {depth} > cap {cap}"

    # c) log it
    log_decision(d)
    last_line = DECISION_LOG.read_text().strip().split("\n")[-1]
    logged = json.loads(last_line)
    assert logged["source"] == "rebalancer"
    assert len(logged["moves"]) == len(d["moves"])

    print("SELF-TEST PASSED")
    print(json.dumps(d, indent=2))
    return d

if __name__ == "__main__":
    self_test()
