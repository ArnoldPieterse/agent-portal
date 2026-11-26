"""convergence_contract.py - Convergence Invariant Contract (Scribe Cycle 26, Goal #2)

Defines "converged" as machine-checkable invariants and evaluates them at each
cycle boundary. Emits a pass/fail token to memory/scribe/convergence-contract.jsonl.

Invariants (>=3 required):
  I1: intervention_count <= BUDGET (default 3 per cycle)
  I2: autonomy_score >= FLOOR (default 60) AND not regressing >5pts from prior cycle
  I3: self_heal_rate >= HEAL_THRESHOLD (default 80%) - failures recovered / failures detected
  I4: no_spo_fresh - no new single-point-of-failure in dependency graph this cycle

Output schema (per line in convergence-contract.jsonl):
  {
    "cycle": int,
    "ts": iso8601,
    "converged": bool,
    "invariants": {
      "I1_interventions_within_budget": {"pass": bool, "value": n, "threshold": n},
      "I2_autonomy_score_healthy": {"pass": bool, "value": float, "floor": float, "delta": float},
      "I3_self_heal_rate": {"pass": bool, "value": float, "threshold": float},
      "I4_no_spo_fresh": {"pass": bool, "detail": str}
    },
    "failing": ["I1...", ...]  // empty if converged
  }

Consumers: Verifier (gate on convergence before certifying), Forge (canary check).
"""
import pathlib, json, sys
from datetime import datetime, timezone

ROOT = pathlib.Path(".")

# === CONFIGURATION ===
BUDGET_INTERVENTIONS = 3   # max interventions per cycle for I1
AUTONOMY_FLOOR = 60.0      # minimum autonomy score for I2
REGRESSION_THRESHOLD = 5.0 # max allowed drop from prior cycle for I2
HEAL_THRESHOLD = 80.0      # min self-heal rate % for I3


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


def get_current_cycle():
    """Determine current cycle number from goal_ledger or autonomy-score."""
    score = load_json("memory/ops/autonomy-score.json")
    if score:
        # Try to infer from intervention data
        pass
    # Fallback: count cycles from intervention patterns
    interventions = load_jsonl("memory/scribe/intervention-patterns.jsonl")
    if interventions:
        return max(iv.get("cycle", 0) for iv in interventions) + 1
    return 1


def check_I1_interventions():
    """I1: intervention_count <= BUDGET"""
    interventions = load_jsonl("memory/scribe/intervention-patterns.jsonl")
    cycle = get_current_cycle()
    # Count interventions for the most recent cycle (or last N if current is 0)
    recent_cycles = [c for c in range(max(1, cycle - 3), cycle + 1)]
    count = sum(1 for iv in interventions if iv.get("cycle", 0) in recent_cycles)
    
    # Use the most recent single cycle for the check
    latest_cycle = max((iv.get("cycle", 0) for iv in interventions), default=0)
    cycle_count = sum(1 for iv in interventions if iv.get("cycle") == latest_cycle)
    
    passed = cycle_count <= BUDGET_INTERVENTIONS
    return {
        "pass": passed,
        "value": cycle_count,
        "threshold": BUDGET_INTERVENTIONS,
        "detail": f"{cycle_count} interventions in cycle {latest_cycle} (budget: {BUDGET_INTERVENTIONS})"
    }


def check_I2_autonomy_score():
    """I2: autonomy_score >= FLOOR AND not regressing >REGRESSION_THRESHOLD"""
    score_data = load_json("memory/ops/autonomy-score.json")
    if not score_data:
        return {"pass": False, "value": 0, "floor": AUTONOMY_FLOOR, "delta": 0,
                "detail": "autonomy-score.json not found"}
    
    current = score_data.get("score", 0)
    
    # Get prior score from trend data if available
    trend = load_jsonl("memory/scribe/autonomy-trend.jsonl")
    delta = 0.0
    if len(trend) >= 2:
        prior = trend[-2].get("score", current)
        delta = current - prior
    
    passed = (current >= AUTONOMY_FLOOR) and (delta >= -REGRESSION_THRESHOLD)
    return {
        "pass": passed,
        "value": current,
        "floor": AUTONOMY_FLOOR,
        "delta": round(delta, 1),
        "detail": f"score={current} (floor={AUTONOMY_FLOOR}), delta={delta:+.1f} (max drop={REGRESSION_THRESHOLD})"
    }


def check_I3_self_heal():
    """I3: self_heal_rate >= HEAL_THRESHOLD"""
    incidents = load_jsonl("memory/ops/incidents.jsonl")
    if not incidents:
        # No incidents = perfect heal rate (vacuously true)
        return {"pass": True, "value": 100.0, "threshold": HEAL_THRESHOLD,
                "detail": "no incidents recorded (vacuous pass)"}
    
    detected = len(incidents)
    recovered = sum(1 for i in incidents if i.get("recovered", False) or i.get("status") == "resolved")
    rate = (recovered / detected * 100) if detected > 0 else 100.0
    
    passed = rate >= HEAL_THRESHOLD
    return {
        "pass": passed,
        "value": round(rate, 1),
        "threshold": HEAL_THRESHOLD,
        "detail": f"{recovered}/{detected} incidents recovered ({rate:.1f}%)"
    }


def check_I4_no_spo_fresh():
    """I4: no new single-point-of-failure this cycle"""
    dep_graph = load_json("memory/scribe/autonomy-dependency-graph.json")
    if not dep_graph:
        # No dependency graph = no known SPOFs (can't detect fresh ones)
        return {"pass": True, "detail": "no dependency graph available (vacuous pass)"}
    
    spofs = dep_graph.get("spof_nodes", [])
    fresh_spofs = [s for s in spofs if s.get("introduced_cycle") == get_current_cycle()]
    passed = len(fresh_spofs) == 0
    return {
        "pass": passed,
        "detail": f"{len(fresh_spofs)} fresh SPOF(s) this cycle" + 
                  (f": {[s.get('id') for s in fresh_spofs]}" if fresh_spofs else "")
    }


def main():
    now = datetime.now(timezone.utc).isoformat()
    cycle = get_current_cycle()
    
    # Evaluate all invariants
    I1 = check_I1_interventions()
    I2 = check_I2_autonomy_score()
    I3 = check_I3_self_heal()
    I4 = check_I4_no_spo_fresh()
    
    invariants = {
        "I1_interventions_within_budget": I1,
        "I2_autonomy_score_healthy": I2,
        "I3_self_heal_rate": I3,
        "I4_no_spo_fresh": I4
    }
    
    failing = [name for name, result in invariants.items() if not result.get("pass", False)]
    converged = len(failing) == 0
    
    # Emit token
    token = {
        "cycle": cycle,
        "ts": now,
        "converged": converged,
        "invariants": invariants,
        "failing": failing
    }
    
    out_path = ROOT / "memory" / "scribe" / "convergence-contract.jsonl"
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(token) + "\n")
    
    # Report
    status = "CONVERGED" if converged else "NOT CONVERGED"
    print(f"Cycle {cycle}: {status}")
    for name, result in invariants.items():
        mark = "PASS" if result.get("pass") else "FAIL"
        print(f"  [{mark}] {name}: {result.get('detail', '')}")
    if failing:
        print(f"  Failing: {failing}")
    print(f"Token written to {out_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
