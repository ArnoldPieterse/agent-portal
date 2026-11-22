"""Model Routing Optimizer - Orchestrator Goal #2
Computes optimal model-to-agent assignments minimizing total VRAM while meeting quality floors.

Usage: python memory/orchestrator/model_router.py [--forecast <path>] [--output <path>]
Output: JSON with assignment table + per-decision rationale.
"""
import json, os, sys, time
from pathlib import Path
from itertools import product

BASE = Path(__file__).resolve().parent.parent.parent  # repo root
MATRIX_PATH = BASE / "memory" / "llm" / "model-capability-matrix.json"
AGENTS_PATH = BASE / "agents.json"

# Quality floors per agent role: minimum capability set + min model tier (0=Q4, 1=Q8)
QUALITY_FLOORS = {
    "Orchestrator": {"min_tier": 1, "required_caps": ["text", "code"]},
    "Researcher":   {"min_tier": 0, "required_caps": ["text", "long-ctx", "rag"]},
    "Builder":      {"min_tier": 1, "required_caps": ["text", "code"]},
    "Verifier":     {"min_tier": 0, "required_caps": ["text", "code"]},
    "Designer":     {"min_tier": 0, "required_caps": ["text"]},
    "Archivist":    {"min_tier": 1, "required_caps": ["text", "long-ctx", "rag"]},
    "Scribe":       {"min_tier": 1, "required_caps": ["text", "code"]},
    "Mechanic":     {"min_tier": 0, "required_caps": ["text", "code"]},
}

# Tier mapping: Q4=0, Q8=1 (higher = more capable)
def model_tier(model):
    if "Q8" in model["id"]:
        return 1
    elif "Q4" in model["id"]:
        return 0
    else:
        return -1  # unknown

def load_matrix():
    with open(MATRIX_PATH) as f:
        return json.load(f)

def load_agents():
    with open(AGENTS_PATH) as f:
        data = json.load(f)
    agents = data if isinstance(data, list) else data.get("agents", [])
    return agents

def get_available_models(matrix):
    """Return models that are actually downloadable/loaded (path not None or already loaded)."""
    avail = []
    for m in matrix["models"]:
        # Only text-capable models for agent routing
        if "text" not in m.get("capabilities", []):
            continue
        # Skip models not yet downloaded
        if m.get("path") is None:
            continue
        avail.append(m)
    return avail

def check_floor(agent_name, model, floors):
    """Check if a model meets the quality floor for an agent."""
    if agent_name not in floors:
        return True  # no floor defined
    floor = floors[agent_name]
    tier = model_tier(model)
    if tier < floor["min_tier"]:
        return False
    caps = set(model.get("capabilities", []))
    for req in floor["required_caps"]:
        if req not in caps:
            return False
    return True

def resolve_alias_to_model(alias, models):
    """Resolve an alias (e.g. 'atlas-q8') to a model ID in the matrix."""
    for m in models:
        if alias in m.get("aliases", []):
            return m["id"]
    # Direct match?
    for m in models:
        if alias == m["id"]:
            return m["id"]
    return None

def compute_vram_usage(assignments, models_by_id, all_models=None):
    """Compute total unique VRAM needed (shared model = counted once per GPU)."""
    # Group by model ID - if multiple agents share same model, it only occupies VRAM once per GPU
    used_models = {}  # model_id -> list of agents
    for agent_name, model_id in assignments.items():
        # Resolve aliases to actual model IDs
        resolved = model_id
        if all_models:
            r = resolve_alias_to_model(model_id, all_models)
            if r:
                resolved = r
        used_models.setdefault(resolved, []).append(agent_name)
    
    total_vram = 0
    details = []
    for mid, agents in used_models.items():
        m = models_by_id.get(mid)
        if m:
            total_vram += m["vram_gb"]
            details.append({"model": mid, "vram_gb": m["vram_gb"], "agents": agents})
    return total_vram, details

def optimize(agents, models, floors):
    """
    Greedy assignment: for each agent (sorted by constraint tightness),
    assign the lowest-VRAM model that meets its quality floor.
    Then try to consolidate (share models) to reduce total VRAM.
    """
    models_by_id = {m["id"]: m for m in models}
    eligible = {}  # agent -> list of eligible model IDs
    
    for a in agents:
        name = a["name"]
        eligible[name] = []
        for m in models:
            if check_floor(name, m, floors):
                eligible[name].append(m["id"])
    
    # Sort agents by number of eligible options (most constrained first)
    sorted_agents = sorted(agents, key=lambda a: len(eligible.get(a["name"], [])))
    
    assignment = {}
    rationale = {}
    
    for a in sorted_agents:
        name = a["name"]
        candidates = eligible.get(name, [])
        if not candidates:
            # No model meets floor - assign best available (highest tier)
            candidates = [m["id"] for m in models]
            rationale[name] = f"WARNING: No model meets quality floor; assigned best available."
        
        # Pick lowest VRAM among eligible
        candidates_sorted = sorted(candidates, key=lambda mid: models_by_id[mid]["vram_gb"])
        chosen = candidates_sorted[0]
        assignment[name] = chosen
        
        if name not in rationale:
            floor = floors.get(name, {})
            tier_info = f"tier>={floor.get('min_tier','?')}" if floor else "no floor"
            rationale[name] = (
                f"Lowest-VRAM model meeting {tier_info} + caps {floor.get('required_caps',[])} "
                f"-> {chosen} ({models_by_id[chosen]['vram_gb']}GB)"
            )
    
    # Consolidation pass: try to merge agents onto same model if it meets both floors
    for i, a1 in enumerate(agents):
        for a2 in agents[i+1:]:
            n1, n2 = a1["name"], a2["name"]
            m1, m2 = assignment[n1], assignment[n2]
            if m1 == m2:
                continue
            # Can we move n1 onto m2?
            if check_floor(n1, models_by_id[m2], floors):
                # Move n1 to m2 (prefer consolidating on lower-VRAM model)
                if models_by_id[m2]["vram_gb"] < models_by_id[m1]["vram_gb"]:
                    assignment[n1] = m2
                    rationale[n1] += f" | Consolidated onto {m2} (shared with {n2}) to save VRAM."
    
    return assignment, rationale

def load_forecast(path):
    """Load capacity forecast if available; else use static baseline."""
    if path and os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    # Static baseline: assume current workload continues
    return {"predicted_demand": "steady", "peak_agents": ["Builder", "Orchestrator"], "note": "No forecast file; using steady-state assumption."}

def main():
    matrix = load_matrix()
    agents = load_agents()
    models = get_available_models(matrix)
    
    if not models:
        print("ERROR: No available text models in capability matrix.", file=sys.stderr)
        sys.exit(1)
    
    # Load forecast (optional)
    forecast_path = None
    if "--forecast" in sys.argv:
        forecast_path = sys.argv[sys.argv.index("--forecast") + 1]
    forecast = load_forecast(forecast_path)
    
    # Run optimizer
    assignment, rationale = optimize(agents, models, QUALITY_FLOORS)
    models_by_id = {m["id"]: m for m in models}
    
    total_vram, vram_details = compute_vram_usage(assignment, models_by_id, models)
    
    # Compare with current (manual) assignment - resolve aliases
    current_assignment = {}
    for a in agents:
        alias = a.get("model_id", "unknown")
        resolved = resolve_alias_to_model(alias, models)
        current_assignment[a["name"]] = resolved if resolved else alias
    current_vram, _ = compute_vram_usage(current_assignment, models_by_id)
    
    # Build output
    output = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "forecast_source": forecast_path or "steady-state (no file)",
        "predicted_demand": forecast.get("predicted_demand", "unknown"),
        "assignment": assignment,
        "total_vram_gb": round(total_vram, 1),
        "current_manual_vram_gb": round(current_vram, 1),
        "vram_delta_pct": round((total_vram - current_vram) / current_vram * 100, 1) if current_vram else 0,
        "vram_breakdown": vram_details,
        "rationale": rationale,
        "quality_floors_met": all(
            check_floor(name, models_by_id.get(mid, {"id":"?","capabilities":[]}), QUALITY_FLOORS)
            for name, mid in assignment.items()
        ),
        "models_available": [m["id"] for m in models],
    }
    
    # Write output
    out_path = BASE / "memory" / "orchestrator" / "model_router_output.json"
    if "--output" in sys.argv:
        out_path = Path(sys.argv[sys.argv.index("--output") + 1])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"Model routing complete -> {out_path}")
    print(f"  Total VRAM (optimized): {total_vram:.1f} GB")
    print(f"  Total VRAM (current):   {current_vram:.1f} GB")
    print(f"  Delta: {output['vram_delta_pct']:+.1f}%")
    print(f"  Quality floors met: {output['quality_floors_met']}")
    
    # Verification check: must be <=10% more VRAM than manual
    if output["vram_delta_pct"] > 10:
        print("  WARNING: Optimized assignment exceeds manual by >10%! Check constraints.")
    else:
        print("  PASS: Within 10% of manual assignment VRAM.")

if __name__ == "__main__":
    main()
