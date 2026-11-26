"""Convergence KPI Rollup - single source of truth for fleet convergence metrics.

Emits one JSON line per cycle to memory/scribe/convergence-kpi.jsonl:
  {cycle, autonomy_score, interventions, cost_min, self_heal_pct, converged, mae, sources}

Every field traces to an existing source file (named in `sources`). No invented numbers.
"""
import json, pathlib, statistics
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # project root
OUT = ROOT / "memory/scribe/convergence-kpi.jsonl"

def load_jsonl(path):
    p = ROOT / path
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    out = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out

def load_json(path):
    p = ROOT / path
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

def get_autonomy_scores():
    """Source: memory/scribe/autonomy-trend.jsonl -> {cycle: score}"""
    entries = load_jsonl("memory/scribe/autonomy-trend.jsonl")
    return {e["cycle"]: e["score"] for e in entries if "cycle" in e and "score" in e}

def get_interventions_per_cycle():
    """Source: memory/ops/human-interventions.jsonl -> {cycle: count}"""
    entries = load_jsonl("memory/ops/human-interventions.jsonl")
    counts = {}
    for e in entries:
        c = e.get("cycle", 0)
        counts[c] = counts.get(c, 0) + 1
    return counts

def get_self_heal_pct():
    """Source: memory/ops/recovery-sla-summary.json -> overall SLA compliance %"""
    data = load_json("memory/ops/recovery-sla-summary.json")
    if not data:
        return None
    types = data.get("types", {})
    total_count = 0
    compliant = 0
    for t, v in types.items():
        cnt = v.get("count", 0)
        sla_pct = v.get("sla_compliance_pct", 0)
        total_count += cnt
        if sla_pct >= 100.0:
            compliant += cnt
    if total_count == 0:
        return None
    return round(100.0 * compliant / total_count, 1)

def get_converged(cycle):
    """Source: memory/scribe/convergence-contract.jsonl -> converged bool for given cycle"""
    entries = load_jsonl("memory/scribe/convergence-contract.jsonl")
    for e in entries:
        if e.get("cycle") == cycle:
            return e.get("converged", None)
    return None

def get_mae():
    """Source: memory/goals/calibration.json -> mean absolute error of forecast hits.
    
    MAE here = 1 - (hit_on_time / total) averaged across runs, scaled to [0,1].
    Lower is better. If no calibration data, return None.
    """
    data = load_json("memory/goals/calibration.json")
    if not data or "runs" not in data:
        return None
    errors = []
    for run in data["runs"]:
        total = run.get("total", 0)
        if total == 0:
            continue
        hit = run.get("hit_on_time", 0)
        # Error rate per run (1 - accuracy)
        err = 1.0 - (hit / total)
        errors.append(err)
    if not errors:
        return None
    return round(statistics.mean(errors), 4)

def get_cost_min(cycle=None):
    """Source: memory/scribe/convergence-velocity.json -> interventions_per_cycle * avg_cycle_duration_min.
    
    We use interventions_per_cycle from velocity as a proxy for cost (minutes of human attention).
    Each intervention ~ 5 min of human time (stated assumption, documented in sources).
    """
    vel = load_json("memory/scribe/convergence-velocity.json")
    if not vel:
        return None
    ipc = vel.get("metrics", {}).get("interventions_per_cycle", None)
    if ipc is None:
        return None
    # Cost = interventions * 5 min each (documented assumption)
    return round(ipc * 5, 2)

def compute_kpis():
    """Compute KPI for ALL cycles with available autonomy score data.
    
    Emits one entry per cycle so the trend has >=2 points when data exists.
    """
    scores = get_autonomy_scores()
    if not scores:
        print("ERROR: no autonomy-trend.jsonl entries found")
        return []
    
    interventions = get_interventions_per_cycle()
    self_heal = get_self_heal_pct()
    mae = get_mae()
    cost_min = get_cost_min(None)  # same for all cycles (velocity-based)
    
    # Get all contract entries for converged lookup
    contracts = load_jsonl("memory/scribe/convergence-contract.jsonl")
    contract_by_cycle = {c["cycle"]: c.get("converged", False) for c in contracts if "cycle" in c}
    
    kpis = []
    now_ts = datetime.now(timezone.utc).isoformat()
    
    for cycle in sorted(scores.keys()):
        converged = contract_by_cycle.get(cycle, None)
        # If no contract entry for this exact cycle, use nearest lower (or None if none)
        if converged is None:
            lower = [c for c in contract_by_cycle if c <= cycle]
            if lower:
                converged = contract_by_cycle[max(lower)]
        
        kpis.append({
            "cycle": cycle,
            "ts": now_ts,
            "autonomy_score": scores[cycle],
            "interventions": interventions.get(cycle, 0),
            "cost_min": cost_min,
            "self_heal_pct": self_heal,
            "converged": converged,
            "mae": mae,
            "sources": {
                "autonomy_score": "memory/scribe/autonomy-trend.jsonl",
                "interventions": "memory/ops/human-interventions.jsonl",
                "cost_min": "memory/scribe/convergence-velocity.json (ipc * 5min assumption)",
                "self_heal_pct": "memory/ops/recovery-sla-summary.json",
                "converged": "memory/scribe/convergence-contract.jsonl",
                "mae": "memory/goals/calibration.json"
            }
        })
    return kpis

def main():
    kpis = compute_kpis()
    if not kpis:
        print("FAILED: could not compute KPIs")
        return 1
    
    # Write all cycles (replace existing file entirely - idempotent)
    lines = [json.dumps(k) for k in kpis]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    
    latest = kpis[-1]
    print(f"OK: {len(kpis)} cycle(s) written to {OUT.relative_to(ROOT)}")
    print(f"  latest cycle {latest['cycle']}: autonomy_score={latest['autonomy_score']}, "
          f"interventions={latest['interventions']}, cost_min={latest['cost_min']}, "
          f"self_heal_pct={latest['self_heal_pct']}, converged={latest['converged']}, mae={latest['mae']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
