"""Fleet Health Composite Gauge - computes a single 0-100 score blending
completion rate, interventions, duration stability, and OOM recovery.

Output: JSON with composite score + component breakdown for tooltip.
Weights sum to 1.0. Run as part of /api/health or standalone.

Formula:
  composite = w1*completion + w2*intervention_score + w3*duration_stability + w4*oom_recovery
  
  completion (w=0.4): fleet_pct_reached directly from goal_ledger.json
  intervention_score (w=0.2): max(0, 100 - interventions_per_cycle * 25)
    Rationale: <4 interventions/cycle = healthy; 8+ = degraded
  duration_stability (w=0.2): avg SLA compliance * trend_penalty
    trend_penalty = 0.9 if any type trending "worsening", else 1.0
  oom_recovery (w=0.2): OOM SLA compliance pct from recovery-sla-summary.json

Usage:
  python memory/builder/fleet_health_gauge.py          # prints JSON to stdout
  python memory/builder/fleet_health_gauge.py --check  # asserts weights sum to 1
"""
import json, sys
from pathlib import Path
from datetime import datetime, timezone

WEIGHTS = {
    "completion": 0.4,
    "interventions": 0.2,
    "duration_stability": 0.2,
    "oom_recovery": 0.2,
}

def get_completion_rate():
    """Read fleet_pct_reached from goal_ledger.json."""
    ledger_path = Path("goal_ledger.json")
    if not ledger_path.exists():
        return 0, {"error": "goal_ledger.json not found"}
    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    pct = data.get("fleet_pct_reached", 0)
    total = data.get("fleet_total_goals", 0)
    reached = data.get("fleet_reached", 0)
    return pct, {"reached": reached, "total": total, "pct": pct}

def get_intervention_score():
    """Score based on interventions per cycle. Fewer = better."""
    intv_path = Path("memory/ops/human-interventions.jsonl")
    if not intv_path.exists():
        return 100, {"count": 0, "per_cycle": 0, "note": "no intervention log"}
    lines = intv_path.read_text(encoding="utf-8").strip().split("\n")
    count = len([l for l in lines if l.strip()])
    
    # Estimate cycles active: from goal_ledger generated date or use cycle range
    # Use the max cycle number found in interventions as a proxy
    max_cycle = 1
    for line in lines:
        if line.strip():
            try:
                d = json.loads(line)
                max_cycle = max(max_cycle, d.get("cycle", 1))
            except (json.JSONDecodeError, ValueError):
                pass
    
    # Cycles span from ~1 to max_cycle; use a baseline of 8 cycles as "normal"
    cycles_active = max(8, max_cycle)
    per_cycle = count / cycles_active if cycles_active > 0 else 0
    
    score = max(0, min(100, 100 - per_cycle * 25))
    return round(score, 1), {"count": count, "cycles_active": cycles_active, "per_cycle": round(per_cycle, 2)}

def get_duration_stability():
    """Avg SLA compliance across incident types, penalized for worsening trends."""
    sla_path = Path("memory/ops/recovery-sla-summary.json")
    if not sla_path.exists():
        return 100, {"note": "no SLA summary; assuming nominal"}
    data = json.loads(sla_path.read_text(encoding="utf-8"))
    types = data.get("types", {})
    if not types:
        return 100, {"note": "empty types"}
    
    compliance_scores = []
    trends = []
    for tname, tdata in types.items():
        compliance_scores.append(tdata.get("sla_compliance_pct", 100))
        trends.append(tdata.get("trend", "stable"))
    
    avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 100
    has_worsening = "worsening" in trends
    penalty = 0.9 if has_worsening else 1.0
    
    score = round(avg_compliance * penalty, 1)
    return score, {
        "avg_compliance_pct": round(avg_compliance, 1),
        "trend_penalty": penalty,
        "trends": dict(zip(types.keys(), trends)),
        "total_incidents": data.get("total_incidents", 0),
    }

def get_oom_recovery():
    """OOM-specific SLA compliance percentage."""
    sla_path = Path("memory/ops/recovery-sla-summary.json")
    if not sla_path.exists():
        return 100, {"note": "no SLA summary; assuming nominal"}
    data = json.loads(sla_path.read_text(encoding="utf-8"))
    oom = data.get("types", {}).get("oom", {})
    if not oom:
        return 100, {"note": "no OOM incidents recorded yet (nominal)"}
    
    score = oom.get("sla_compliance_pct", 100)
    return score, {
        "count": oom.get("count", 0),
        "recovery_mean_min": oom.get("recovery_mean_min"),
        "sla_target_recovery_min": oom.get("sla_target_recovery_min"),
        "trend": oom.get("trend", "stable"),
    }

def compute():
    """Compute the composite gauge score."""
    completion, comp_detail = get_completion_rate()
    interventions, intv_detail = get_intervention_score()
    duration_stability, ds_detail = get_duration_stability()
    oom_recovery, oom_detail = get_oom_recovery()
    
    components = {
        "completion": {"score": completion, "weight": WEIGHTS["completion"], "detail": comp_detail},
        "interventions": {"score": interventions, "weight": WEIGHTS["interventions"], "detail": intv_detail},
        "duration_stability": {"score": duration_stability, "weight": WEIGHTS["duration_stability"], "detail": ds_detail},
        "oom_recovery": {"score": oom_recovery, "weight": WEIGHTS["oom_recovery"], "detail": oom_detail},
    }
    
    composite = sum(components[k]["score"] * components[k]["weight"] for k in components)
    
    return {
        "composite_score": round(composite, 1),
        "components": components,
        "weights_sum": round(sum(WEIGHTS.values()), 2),
        "generated": datetime.now(timezone.utc).isoformat(),
        "formula": "0.4*completion + 0.2*intervention_score + 0.2*duration_stability + 0.2*oom_recovery",
    }

def main():
    if "--check" in sys.argv:
        assert abs(sum(WEIGHTS.values()) - 1.0) < 0.001, f"Weights don't sum to 1: {sum(WEIGHTS.values())}"
        result = compute()
        assert 0 <= result["composite_score"] <= 100, f"Score out of range: {result['composite_score']}"
        print("CHECK PASS: weights sum to 1, score in [0,100]")
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(compute(), indent=2))

if __name__ == "__main__":
    main()
