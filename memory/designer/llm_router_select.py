"""
LLM Router - Auto-Select Algorithm
===================================
Picks the best model for a given task + agent profile.
Pure logic module: no I/O, no network calls. Caller handles hotload/evict.

Usage:
    from llm_router_select import select_model
    result = select_model(task_caps, agent_profile, loaded_models, matrix)
    # result = {"model_id": "Q4_K_S", "score": 0.82, "reason": "...", "needs_hotload": False}
"""

import json
from pathlib import Path
from typing import Optional


def load_matrix() -> dict:
    """Load the capability matrix SSOT."""
    path = Path(__file__).parent.parent / "llm" / "model-capability-matrix.json"
    with open(path) as f:
        return json.load(f)


def select_model(
    task_capabilities: list[str],
    agent_profile: dict,
    loaded_models: list[dict],  # [{"id": ..., "loaded": True, "gpu": 0}, ...]
    matrix: Optional[dict] = None,
) -> dict:
    """
    Select the best model for a task.
    
    Args:
        task_capabilities: list of capability tags required (e.g. ["text", "video"])
        agent_profile: the agent's entry from agents.json (with extended fields)
        loaded_models: current resident models from GET /models
        matrix: capability matrix (loaded if None)
    
    Returns:
        {"model_id": str, "score": float, "reason": str, "needs_hotload": bool, "evict_target": Optional[str]}
    """
    if matrix is None:
        matrix = load_matrix()
    
    weights = matrix["selection_weights"]
    models = matrix["models"]
    
    # For per-task selection, match against TASK capabilities only.
    # Agent's required_caps define eligibility for DEFAULT binding, not per-task dispatch.
    # A specialized model (e.g. SDXL) doesn't need to do 'text' - it receives text prompts.
    required_caps = set(task_capabilities) if task_capabilities else set(agent_profile.get("required_caps", ["text"]))
    
    candidates = []
    for model in models:
        # Skip models not yet downloaded
        if model["path"] is None and model["id"] not in {
            m["id"] for m in loaded_models if m.get("loaded")
        }:
            continue  # can't load what isn't on disk (unless already resident)
        
        model_caps = set(model["capabilities"])
        
        # Hard filter: must support ALL required capabilities
        if not required_caps.issubset(model_caps):
            continue
        
        # Hard filter: context length
        min_ctx = agent_profile.get("min_context", 0)
        if model["max_context"] and model["max_context"] < min_ctx:
            continue
        
        # Score the candidate
        score = _score_candidate(model, required_caps, loaded_models, weights, matrix)
        candidates.append((model["id"], score))
    
    if not candidates:
        return {
            "model_id": None,
            "score": 0.0,
            "reason": f"No local model supports {sorted(required_caps)}",
            "needs_hotload": False,
            "evict_target": None,
            "fallback": "remote",  # cascade to remote hosts
        }
    
    # Sort by score descending
    candidates.sort(key=lambda x: x[1], reverse=True)
    best_id, best_score = candidates[0]
    
    # Determine if hotload is needed
    loaded_ids = {m["id"] for m in loaded_models if m.get("loaded")}
    needs_hotload = best_id not in loaded_ids
    
    # If hotload needed, find who to evict (lowest-priority resident model)
    evict_target = None
    if needs_hotload:
        evict_target = _find_eviction_candidate(loaded_models, agent_profile, matrix)
    
    reason = _build_reason(best_id, required_caps, loaded_ids, weights)
    
    return {
        "model_id": best_id,
        "score": round(best_score, 3),
        "reason": reason,
        "needs_hotload": needs_hotload,
        "evict_target": evict_target,
    }


def _score_candidate(model, required_caps, loaded_models, weights, matrix) -> float:
    """Compute selection score for one model."""
    # 1. Capability match (0.6): how many of the model's caps overlap with required
    model_caps = set(model["capabilities"])
    cap_score = len(required_caps & model_caps) / max(len(required_caps), 1)
    
    # 2. Residency bonus (0.2): already loaded = free
    loaded_ids = {m["id"] for m in loaded_models if m.get("loaded")}
    residency_score = 1.0 if model["id"] in loaded_ids else 0.0
    
    # 3. Context fit (0.1): larger ctx is better but diminishing returns
    ctx = model.get("max_context") or 0
    if ctx >= 65536:
        ctx_score = 1.0
    elif ctx >= 32768:
        ctx_score = 0.7
    else:
        ctx_score = 0.4
    
    # 4. Cost inverse (0.1): smaller models are "cheaper" (faster, less VRAM)
    all_vram = [m["vram_gb"] for m in matrix["models"] if m["vram_gb"]]
    min_v, max_v = min(all_vram), max(all_vram)
    if max_v > min_v:
        cost_score = 1.0 - (model["vram_gb"] - min_v) / (max_v - min_v)
    else:
        cost_score = 0.5
    
    return (
        cap_score * weights["capability_match"]
        + residency_score * weights["residency_bonus"]
        + ctx_score * weights["context_fit"]
        + cost_score * weights["cost_inverse"]
    )


def _find_eviction_candidate(loaded_models, agent_profile, matrix) -> Optional[str]:
    """
    Find which loaded model to evict to make room.
    Strategy: evict the model with no active agent binding AND lowest priority.
    """
    # Models that are bound to an active agent (from aliases in matrix)
    bound_ids = set()
    for m in matrix["models"]:
        if any(a == agent_profile.get("model_id") for a in m.get("aliases", [])):
            bound_ids.add(m["id"])
    
    # Prefer evicting unbound models
    for lm in loaded_models:
        if not lm.get("loaded"):
            continue
        if lm["id"] not in bound_ids:
            return lm["id"]
    
    # All are bound - evict the smallest (least VRAM impact to restore)
    loaded = [lm for lm in loaded_models if lm.get("loaded")]
    if loaded:
        loaded.sort(key=lambda m: matrix["models"][
            next((x["id"] for x in matrix["models"] if x["id"] == m["id"]), {"vram_gb": 999})
        ]["vram_gb"]
        )
        return loaded[0]["id"]
    
    return None


def _build_reason(model_id, required_caps, loaded_ids, weights) -> str:
    """Human-readable explanation of the selection."""
    parts = [f"matches {sorted(required_caps)}"]
    if model_id in loaded_ids:
        parts.append("already resident (no hotload needed)")
    else:
        parts.append("requires hotload")
    return "; ".join(parts)


# --- Quick self-test ---
if __name__ == "__main__":
    matrix = load_matrix()
    
    # Simulate: Researcher needs long-context text analysis
    agent = {"id": "researcher", "model_id": "quinn-q4", "required_caps": ["text"], "min_context": 32768}
    loaded = [{"id": "Q4_K_S", "loaded": True, "gpu": 0}, {"id": "Q8_0", "loaded": True, "gpu": 1}]
    
    result = select_model(["text", "long-ctx"], agent, loaded, matrix)
    print(f"Researcher + long-ctx text → {result['model_id']} (score={result['score']}, hotload={result['needs_hotload']})")
    print(f"  Reason: {result['reason']}")
    
    # Simulate: task needs video gen
    agent_v = {"id": "builder", "model_id": "Q8_0", "required_caps": ["text"], "min_context": 16384}
    result2 = select_model(["video", "text"], agent_v, loaded, matrix)
    print(f"\nBuilder + video → {result2['model_id']} (score={result2['score']}, hotload={result2['needs_hotload']})")
    print(f"  Reason: {result2['reason']}")
    if result2.get("fallback"):
        print(f"  Fallback: {result2['fallback']} (no local model with video cap)")
