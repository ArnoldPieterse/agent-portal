# LLM Router & Hotload - Prototype Evidence (2026-11-17)

## What was built
1. **UI prototype** (rendered via render_html): Full dashboard with GPU model slots, agent bindings, auto-select router log, hotload queue, capability matrix, system state. Modes: Manual / Auto-Select / Cascade.
2. **Auto-select algorithm** (`memory/designer/llm_router_select.py`): Pure Python scoring module. 6/6 tests pass.
   - Scores: capability_match(0.6) + residency_bonus(0.2) + ctx_fit(0.1) + cost_inverse(0.1)
   - Cascade fallback to remote hosts when no local match
   - Eviction candidate selection (prefer unbound models)
3. **Capability matrix SSOT** (`memory/llm/model-capability-matrix.json`): 5 models defined (2 local, 3 future), capability tags, VRAM, load times, host info, selection weights.
4. **Architecture spec** (`memory/designer/llm-router-architecture.md`): Full design doc with API endpoints, file structure, hotload procedure integration, mode toggles.

## Key design decisions
- Per-task selection uses TASK capabilities only (not agent baseline union) — allows specialized models like SDXL to be selected for image tasks without requiring text capability
- Cascade: local Q4 → local Q8 → remote hosts → queue+notify
- Idle gate preserved from existing backend-swap procedure (max 3 min wait)
- Agent profile extension: `capabilities[]`, `required_caps[]`, `preferred_class`, `hot` (bool), `ttl_minutes`

## Test results (all pass)
```
Test 1: Researcher + long-ctx → Q4_K_S (0.974, no hotload) ✓
Test 2: Video task → None (fallback=remote) ✓
Test 3: Code fix → Q4_K_S (0.974) ✓
Test 4: Image gen + SDXL resident → SDXL (0.935, no hotload) ✓
Test 5: Image gen + SDXL not loaded → None (can't load undiscovered model) ✓
Test 6: No task caps → agent default → Q4_K_S (0.974) ✓
```

## Next steps (for Builder/Orchestrator)
- Integrate `llm_router_select.py` into `agent_portal.py` as `/api/llm-router/select` endpoint
- Extend `agents.json` with new fields (capabilities, hot, ttl_minutes)
- Add hotload queue state file + idle-gate integration with existing backend-swap procedure
- Build the UI panel into the portal (ui/llm-router.js) using the prototype as reference
- Download future models (Qwen2.5-VL-72B, SDXL, CogVideoX) when capability needed
