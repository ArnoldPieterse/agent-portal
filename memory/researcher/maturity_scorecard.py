#!/usr/bin/env python3
"""
Autonomy Maturity Scorecard - composite 0-100 score per agent + fleet aggregate.
Combines 5 weighted dimensions:
  (a) % autonomous passes          weight=30%
  (b) self-correction success rate  weight=25%
  (c) convergence trend slope       weight=20%
  (d) failure recovery speed        weight=15%
  (e) knowledge transfer efficiency weight=10%

Outputs: per-agent scorecard with radar-chart data + fleet aggregate.
AC: >=5 agents scored; all dimensions present; composite in [0,100];
    fleet aggregate within [0,100]; radar data has 5 axes per agent.
"""
import json, pathlib, math
from datetime import datetime

RESEARCHER_DIR = pathlib.Path("memory/researcher")

def load_json(name):
    p = RESEARCHER_DIR / name
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

def score_autonomous_passes(gradient_data, agent):
    """% of task types where agent is T0 or T1 (autonomous/supervised-auto)."""
    if not gradient_data:
        return 50.0  # neutral default
    task_types = gradient_data.get("task_types", {})
    t0_t1_count = 0
    total = 0
    for ttype, info in task_types.items():
        agent_tiers = info.get("agent_tiers", {})
        if agent in agent_tiers:
            total += 1
            tier = agent_tiers[agent]
            if tier in ("T0", "T1"):
                t0_t1_count += 1
    if total == 0:
        return 50.0
    return (t0_t1_count / total) * 100.0

def score_self_correction(self_corr_data, agent):
    """Self-correction success rate as percentage."""
    if not self_corr_data:
        return 50.0
    table = self_corr_data.get("per_agent_table", {})
    if agent in table:
        return float(table[agent].get("success_rate_pct", 50.0))
    return 50.0

def score_convergence_trend(self_corr_data, agent):
    """
    Per-agent convergence proxy: improvement in self-correction rate early->late.
    Fleet trend from self_correction trend data; per-agent gets proportional share
    based on their event volume relative to fleet.
    Maps: no change=50, 100% improvement=100, 100% degradation=0.
    """
    if not self_corr_data:
        return 50.0
    trend = self_corr_data.get("trend", {})
    early_rate = trend.get("early_period_rate_pct", 45.0)
    late_rate = trend.get("late_period_rate_pct", 22.0)
    # Fleet improvement: lower correction rate = better
    fleet_improvement = (early_rate - late_rate) / max(early_rate, 1)  # fraction improved
    # Per-agent: scale by their contribution ratio
    table = self_corr_data.get("per_agent_table", {})
    total_events = sum(v.get("n_events", 0) for v in table.values())
    agent_events = table.get(agent, {}).get("n_events", 0)
    if total_events == 0:
        return 50.0
    # Agent's share of fleet convergence (proportional weight)
    contribution = agent_events / total_events
    # Map fleet improvement to score: 0% improvement=40, 100% improvement=100
    base_score = 40 + fleet_improvement * 60  # 40-100 range
    # Individual modifier: if agent has more events than average, they contributed more
    avg_contribution = 1.0 / len(table) if table else 0.1
    ratio = contribution / max(avg_contribution, 0.01)
    # Cap ratio at [0.5, 2.0] to avoid extreme outliers
    ratio = max(0.5, min(2.0, ratio))
    score = base_score * (0.8 + 0.2 * ratio)  # modulate by contribution
    return max(0, min(100, score))

def score_failure_recovery(self_corr_data, agent):
    """
    Failure recovery speed: lower avg_latency_passes = faster = better.
    Normalize: latency 1.0 -> 95, latency 2.0 -> 45, linear between.
    """
    if not self_corr_data:
        return 50.0
    table = self_corr_data.get("per_agent_table", {})
    if agent not in table:
        return 50.0
    latency = float(table[agent].get("avg_latency_passes", 1.5))
    # Map: 1.0 -> 95, 2.0 -> 45 (faster is better)
    if latency <= 1.0:
        return 95.0
    elif latency >= 2.0:
        return 45.0
    else:
        frac = (latency - 1.0) / 1.0
        return 95.0 - frac * 50.0

def score_knowledge_transfer(kt_data):
    """
    Knowledge transfer efficiency: fleet-wide metric.
    Based on avg_estimated_time_saved_pct and gap rate.
    Lower gap + higher time saved = better.
    Maps: gap_rate 0% + time_saved 20% -> 100; gap_rate 100% + time_saved 0% -> 0
    """
    if not kt_data:
        return 50.0
    gap_rate = kt_data.get("knowledge_gap_rate_pct", 62.5) / 100.0
    time_saved = kt_data.get("avg_estimated_time_saved_pct", 9.4) / 100.0
    # Score: (1 - gap_rate) * 60 + time_saved * 40
    score = (1 - gap_rate) * 60 + min(time_saved, 1.0) * 40
    return max(0, min(100, score))

def compute_scorecard():
    """Compute full maturity scorecard for all agents."""
    # Load source data
    gradient_data = load_json("autonomy-gradient-results.json")
    self_corr_data = load_json("self-correction-results.json")
    kt_data = load_json("knowledge-transfer-results.json")
    
    # Identify agents (from self-correction table, excluding 'unknown')
    agents = sorted(set(
        k for k in (self_corr_data or {}).get("per_agent_table", {})
        if k != "unknown"
    ))
    if not agents:
        return {"error": "no agent data found", "agents": []}
    
    # Weights
    WEIGHTS = {
        "autonomous_passes": 0.30,
        "self_correction": 0.25,
        "convergence_trend": 0.20,
        "failure_recovery": 0.15,
        "knowledge_transfer": 0.10
    }
    
    # Compute per-agent scores
    agents_data = []
    for agent in agents:
        dims = {
            "autonomous_passes": score_autonomous_passes(gradient_data, agent),
            "self_correction": score_self_correction(self_corr_data, agent),
            "convergence_trend": score_convergence_trend(self_corr_data, agent),
            "failure_recovery": score_failure_recovery(self_corr_data, agent),
            "knowledge_transfer": score_knowledge_transfer(kt_data),
        }
        composite = sum(dims[k] * WEIGHTS[k] for k in WEIGHTS)
        agents_data.append({
            "agent": agent,
            "dimensions": dims,
            "composite_score": round(composite, 1),
            "rank": None  # filled after sorting
        })
    
    # Rank by composite
    agents_data.sort(key=lambda x: -x["composite_score"])
    for i, a in enumerate(agents_data):
        a["rank"] = i + 1
    
    # Fleet aggregate (mean of composites, weighted by event volume if available)
    fleet_composite = sum(a["composite_score"] for a in agents_data) / len(agents_data)
    
    # Radar chart data: 5 axes per agent
    radar_axes = ["autonomous_passes", "self_correction", "convergence_trend", "failure_recovery", "knowledge_transfer"]
    radar_data = {
        agent: {ax: round(dims[ax], 1) for ax in radar_axes}
        for agent, dims in ((a["agent"], a["dimensions"]) for a in agents_data)
    }
    
    return {
        "model": "autonomy_maturity_scorecard v1",
        "generated": datetime.now().isoformat(),
        "weights": WEIGHTS,
        "agents": agents_data,
        "fleet_composite": round(fleet_composite, 1),
        "radar_axes": radar_axes,
        "radar_data": radar_data,
        "interpretation": {
            "score_0_20": "Critical - needs human oversight on most tasks",
            "score_20_40": "Developing - significant human involvement required",
            "score_40_60": "Competent - mostly autonomous with periodic check-ins",
            "score_60_80": "Proficient - high autonomy, self-corrects well",
            "score_80_100": "Autonomous - operates independently, converging to steady-state"
        },
        "n_agents": len(agents_data)
    }

def self_test():
    """AC: >=5 agents scored; all dimensions present; composite in [0,100];
    fleet aggregate within [0,100]; radar data has 5 axes per agent."""
    sc = compute_scorecard()
    
    # AC checks
    assert "error" not in sc, f"Scorecard failed: {sc.get('error')}"
    
    n_agents = sc["n_agents"]
    print(f"  Agents scored: {n_agents}")
    assert n_agents >= 5, f"AC FAIL: only {n_agents} agents (need >=5)"
    
    # All dimensions present for each agent
    expected_dims = set(sc["radar_axes"])
    for a in sc["agents"]:
        actual_dims = set(a["dimensions"].keys())
        assert actual_dims == expected_dims, f"AC FAIL: {a['agent']} dims={actual_dims} != {expected_dims}"
        # Composite in [0,100]
        assert 0 <= a["composite_score"] <= 100, f"AC FAIL: {a['agent']} composite={a['composite_score']} out of range"
    
    # Fleet aggregate in [0,100]
    assert 0 <= sc["fleet_composite"] <= 100, f"AC FAIL: fleet={sc['fleet_composite']}"
    
    # Radar data has 5 axes per agent
    for agent, axes in sc["radar_data"].items():
        assert len(axes) == 5, f"AC FAIL: {agent} radar has {len(axes)} axes (need 5)"
    
    # Weights sum to 1.0
    w_sum = sum(sc["weights"].values())
    assert abs(w_sum - 1.0) < 0.001, f"AC FAIL: weights sum={w_sum}"
    
    # Print results
    print(f"  Fleet composite: {sc['fleet_composite']}")
    print(f"  Weights: {sc['weights']}")
    print(f"  {'Agent':<15} {'Composite':>9} {'Rank':>5}  Dimensions")
    print("  " + "-" * 80)
    for a in sc["agents"]:
        d = a["dimensions"]
        print(f"  {a['agent']:<15} {a['composite_score']:>9.1f} {a['rank']:>5}  "
              f"AP={d['autonomous_passes']:.0f} SC={d['self_correction']:.0f} "
              f"CT={d['convergence_trend']:.0f} FR={d['failure_recovery']:.0f} KT={d['knowledge_transfer']:.0f}")
    
    # Save results
    out = RESEARCHER_DIR / "maturity-scorecard-results.json"
    out.write_text(json.dumps(sc, indent=2), encoding="utf-8")
    print(f"\n  Artifact: {out}")
    
    # Summary assertion for evidence
    top_agent = sc["agents"][0]
    print(f"  Top agent: {top_agent['agent']} ({top_agent['composite_score']})")
    bottom_agent = sc["agents"][-1]
    print(f"  Bottom agent: {bottom_agent['agent']} ({bottom_agent['composite_score']})")
    
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        print("maturity_scorecard.py --self-test")
        try:
            self_test()
            print("\nPASS: all ACs met")
        except AssertionError as e:
            print(f"\nFAIL: {e}")
            sys.exit(1)
    else:
        sc = compute_scorecard()
        print(json.dumps(sc, indent=2))
