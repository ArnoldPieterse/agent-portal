# LLM Router & Hotload Architecture
Last updated: 2026-11-17. Owner: Designer (UI) + Orchestrator (logic) + Mechanic (infra).
Status: PROTOTYPE rendered + spec drafted.

## Goal
Auto-select the right LLM model per task, hotload it at runtime without restart,
and bind each agent profile to the model class that matches its capability needs.
Not all agents need a resident model simultaneously — Orchestrator/Scribe manage
which agents are "hot" (model loaded) vs "cold" (model evicted, ready to reload).

## Core Concepts

### 1. Model Slots (per host)
Each GPU slot holds one model at a time. White: 2x 5090 = 2 slots.
- Slot state: `loaded` | `loading` | `unloaded` | `evicting`
- VRAM budget per slot: 51 GB (minus OS/driver overhead ~2 GB)
- Load time varies by model size (15s for SDXL → 600s for 72B VL)

### 2. Agent Profiles (agents.json extension)
Each agent gains:
```json
{
  "id": "designer",
  "model_id": "designer-q4",       // alias to load
  "capabilities": ["text", "image-gen"],  // what this agent CAN do
  "required_caps": ["text"],         // minimum to function
  "preferred_class": "q4",           // q4 | q8 | vl-72b | sdxl | cogvideox
  "min_context": 32768,              // minimum ctx needed
  "hot": true,                       // model is resident (vs cold/evicted)
  "ttl_minutes": 10                  // evict after this idle period
}
```

### 3. Auto-Select Algorithm
When a task arrives for agent X:
1. **Capability match**: filter models where `model.caps ⊇ agent.required_caps ∪ task.extra_caps`
2. **Residency bonus**: if the matched model is already loaded → score +0.2 (no hotload needed)
3. **Context fit**: if `task.estimated_tokens > model.ctx` → reject
4. **Cost inverse**: prefer smaller/faster models for simple tasks (Q4 over Q8 for short code fixes)
5. **VRAM feasibility**: if loading requires eviction, check the target slot has room after evicting idle model

Score formula: `score = (cap_match × 0.6) + (residency × 0.2) + (ctx_fit × 0.1) + (cost_inv × 0.1)`

### 4. Hotload Procedure (per existing backend-swap-procedure.md)
```
request_load(model, gpu_slot):
  1. IDLE GATE: poll /api/inference/active-generations until count==0 (max 3 min)
  2. If target slot occupied by idle model → POST /api/inference/unload {model_path}
  3. Wait for VRAM release (poll nvidia-smi or /models loaded=false)
  4. POST /api/inference/load {model_path, gguf_variant, gpu_ids, max_seq_length, ...}
  5. Poll GET /models until loaded=true (timeout: model-specific, see capability matrix)
  6. Verify alias still points to correct path
  7. Mark agent.hot = true in agents.json
```

### 5. Cascade Fallback
If no local model matches:
1. Check remote hosts (Red :8888, Pale :8888) via their /models endpoints
2. If a remote has the capability → route request there (higher latency but no hotload)
3. If nothing available → queue task + notify Orchestrator with exact unblock step

### 6. Mode Toggles (UI control)
- **Manual**: human picks model per agent; router only validates fit
- **Auto-Select**: router picks best model per task; hotloads if needed
- **Cascade**: start with cheapest capable model; escalate if quality insufficient (e.g. Q4 → Q8 → remote)

## UI Components (rendered in prototype)
1. **GPU Model Slots** - live VRAM usage, load state dots, capacity bars
2. **Agent Bindings** - agent→model map with capability tags, hot/cold status
3. **Auto-Select Router** - last N decisions with task → model → reasoning
4. **Hotload Queue** - pending load/evict operations with progress + idle gate status
5. **Capability Matrix** - model × capability lookup table (drives selection)
6. **System State** - host info, active generations, gate status, last hotload timestamp

## File Structure (proposed)
```
memory/designer/
  llm-router-architecture.md    ← this file
  llm-router-ui.html            ← standalone prototype (rendered above)
memory/llm/
  model-capability-matrix.json  ← SSOT for model caps, VRAM, load times
  hotload-queue.json            ← live queue state (written by router logic)
agents.json                     ← extended with capabilities[], hot, ttl_minutes
agent_portal.py                 ← new endpoints: /api/llm-router/*
```

## API Endpoints (to implement in agent_portal.py)
- `GET /api/llm-router/state` → {slots[], queue[], mode, active_gens}
- `POST /api/llm-router/select` body: {agent_id, task_desc, extra_caps[]} → {model, score, reason, needs_hotload}
- `POST /api/llm-router/hotload` body: {model_id, gpu_slot} → {status, eta_sec}
- `POST /api/llm-router/evict` body: {model_id} → {status}
- `PUT /api/llm-router/mode` body: {mode: "manual"|"auto"|"cascade"} → {ok}
- `GET /api/llm-router/capability-matrix` → full matrix JSON

## Future Extensions
- Video generation agents (CogVideoX, Qwen-VL for 3D scene description)
- 3D environment agents (text-to-3D pipelines, Blender MCP integration)
- Multi-host federation: Router sees all 4 hosts' slots as one pool
- Learning: track task→model success rate; adjust scores over time
- Pre-warm: predict next agent's needs from TODO.md and pre-load in background
