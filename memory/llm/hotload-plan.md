# Hotload & Auto LLM Selector — Design Plan
Last updated: 2026-11-17 (Scribe synthesis; human directive + research pass)
Owner: Scribe (plan) / Orchestrator (execution) / Mechanic (ops plumbing)
Status: PLANNED — not yet built

## 1. Problem Statement
The fleet currently runs 8 agents across 4 hosts, each permanently bound to a model alias.
This wastes VRAM on idle agents and prevents loading specialized models (video gen, 3D,
larger-context) that don't fit the dual-resident Q4+Q8 pattern.

Goal: a system where Scribe+Orchestrator decide which agents are "hot" per round,
the portal hotloads only their required LLMs, and unneeded models are evicted to free
VRAM for specialized workloads (video/3D gen, 256k+ context, etc.).

## 2. Research Findings (2026-11-17)
Sources: zylos.ai model-routing survey (Mar 2026), LM Studio REST API docs, arxiv RouteLLM/MasRouter/Router-R1.

### Routing strategies relevant to our fleet
| Strategy | Fit for us | Notes |
|----------|-----------|-------|
| Static routing (task->model table) | HIGH | agents.json already IS a static routing table; extend with capability tags |
| Classifier-based (RouteLLM) | LOW | overkill for 8 known agents; we know which model each agent needs |
| Cascading/fallback | MEDIUM | useful for quality escalation (Q4->Q8 if Q4 output is weak) |
| Semantic routing | MEDIUM | could auto-classify incoming tasks to the right specialist agent |
| Multi-model ensemble (Router-R1) | LOW | too expensive; we have VRAM constraints |

**Key insight:** Our problem is NOT "which model answers this query best" — it's
"which agents are needed for this round, and can their models fit in VRAM simultaneously?"
This is a resource-scheduling problem, not a routing problem. The static table (agents.json)
is the right primitive; we need a scheduler around it.

### LM Studio API capabilities (verified from docs 2026-11-17)
- `POST /api/v1/models/load` — load with context_length, flash_attention, eval_batch_size, num_experts, offload_kv_cache_to_gpu
- `POST /api/v1/models/unload` — unload by model id
- `GET /api/v1/models` — list all models + loaded state
- Load is ASYNC (returns 200 ack; poll until resident) — confirmed by our backend-swap drill
- Multi-model fit mode: PUT /api/settings/multi-model {enabled:true, mode:"fit"} allows co-residency when VRAM permits

### What's already in place (reusable)
- Backend-swap procedure (memory/llm/backend-swap-procedure.md): idle gate -> load -> verify -> unload, proven zero-binding-loss
- Alias system: path-bound, survives eviction; agents.json model_id resolves via /api/settings/model-aliases
- Per-host Studio API endpoints + auth (agents.json studio/api_key fields)
- WinRM remote exec for hosts without LAN-exposed :8888

## 3. Architecture Design

### 3.1 Agent Activation Model
Each agent gets a lifecycle state:
```
COLD    -> model not loaded; agent can be "woken" by Orchestrator
HOT     -> model resident in VRAM; agent participates in current round
SLEEP   -> model was hot but round ended; TTL countdown before eviction to COLD
```

Transition rules:
- COLD -> HOT: Orchestrator declares agent active for a round; portal triggers load
- HOT -> SLEEP: round completes; agent's generation handle released
- SLEEP -> COLD: TTL expires (default 5 min) OR VRAM pressure from a new load request
- HOT -> COLD: forced eviction when a higher-priority model needs the GPU slot

### 3.2 Model Registry (extends agents.json)
Add per-agent model spec fields:
```json
{
  "id": "scribe",
  "model_id": "scribe-q8",
  "model_spec": {
    "min_context": 32768,
    "vram_gb": 30.1,
    "gpu_count": 1,
    "capabilities": ["text", "vision"],
    "load_time_s": 240,
    "priority": 2
  }
}
```
- `priority`: 1 = always-resident (Orchestrator), 2 = core team, 3 = on-demand specialist
- `capabilities`: tags for the selector (text, vision, video_gen, 3d_gen, code, math)
- `load_time_s`: expected cold-load duration (for scheduling estimates)

### 3.3 Hotload Scheduler (new module: model_scheduler.py)
Lives in the portal process. Responsibilities:
1. **Plan**: given the set of agents Orchestrator wants hot this round, compute a load plan
   - Check VRAM budget per host (from nvidia-smi or /api/v1/models loaded states)
   - Determine which models are already resident vs need loading
   - Identify conflicts (two 30GB models on one 64GB host = OK; three = not)
   - Produce ordered load/unload sequence respecting idle gates

2. **Execute**: run the plan via Studio API calls per host
   - Idle gate: wait for active-generations count == 0 on affected hosts
   - Load: POST /api/v1/models/load with agent's model_spec params
   - Poll until resident (timeout = load_time_s * 2)
   - Unload evicted models after confirming new ones are resident

3. **Report**: log every transition with timestamps to memory/llm/hotload-log.jsonl
   - {ts, host, agent, action: "load"|"unload", model, duration_s, vram_before, vram_after}

### 3.4 Portal API Endpoints (new)
```
POST /api/fleet/activate    body: {agents: ["scribe","builder"], host?: "white"}
  -> triggers scheduler.plan() + execute() for those agents
  -> returns {plan: [...], status: "loading"|"ready", eta_s}

POST /api/fleet/deactivate  body: {agents: ["scribe"]}
  -> marks SLEEP; actual unload deferred to TTL or next VRAM pressure

GET  /api/fleet/status      -> per-host: loaded models, VRAM used/free, hot agents, cold agents
GET  /api/fleet/plan        body: {agents: [...]} -> dry-run: what would load/unload, fits?
```

### 3.5 Specialized Model Slots
For non-chat workloads (video gen, 3D env), define "task models" separate from agent models:
```json
// model_registry.json (new file, fleet-level)
{
  "task_models": [
    {
      "id": "video-gen-1",
      "path": "C:\Users\<white>\.lmstudio\models\stability\SDXL-video...",
      "vram_gb": 24,
      "gpu_count": 1,
      "capabilities": ["video_gen"],
      "exclusive": true  // cannot co-reside with anything
    }
  ]
}
```
- `exclusive: true` means the scheduler must evict ALL other models on that GPU before loading
- Task models are NOT bound to agents; they're loaded on-demand by any agent that needs them
- Orchestrator declares "agent X needs task_model Y for this round" -> scheduler handles eviction

### 3.6 Scribe + Orchestrator Management Protocol
Per round, Orchestrator (or Scribe on its behalf) declares the active set:
1. Orchestrator reads the round's task requirements
2. Determines which agents are needed (by capability match)
3. Calls POST /api/fleet/activate with that set
4. Portal scheduler loads required models, evicts unneeded ones
5. Round runs with only the hot agents in the group prompt
6. After round: POST /api/fleet/deactivate for agents no longer needed

Scribe's role: maintain the model_registry.json, track load/unload history,
flag VRAM pressure warnings before they cause failures.

## 4. Implementation Phases

### Phase 1: Foundation (Builder + Mechanic)
- [ ] Extend agents.json with model_spec fields for all 8 agents
- [ ] Create model_scheduler.py module (plan + execute + report)
- [ ] Add /api/fleet/status endpoint (read-only, shows current state)
- [ ] Unit test: plan() correctly identifies load/unload needs given a target set

### Phase 2: Activation (Builder + Orchestrator)
- [ ] Implement POST /api/fleet/activate with idle gate + load sequence
- [ ] Implement POST /api/fleet/deactivate with TTL-based SLEEP
- [ ] Integrate with round lifecycle: portal auto-deactivates agents after round ends
- [ ] Integration test on White: activate 2 agents, verify models loaded; deactivate, verify unload

### Phase 3: Specialized Models (Mechanic + Builder)
- [ ] Create model_registry.json with task_model schema
- [ ] Implement exclusive eviction logic in scheduler
- [ ] Test: load a large model that requires evicting both resident models on a host
- [ ] Document VRAM budgets per host (nvidia-smi snapshot as baseline)

### Phase 4: Auto-selection (Scribe + Orchestrator)
- [ ] Implement capability-based auto-matching: given a task description, suggest agent set
- [ ] Add /api/fleet/plan dry-run endpoint for pre-flight checks
- [ ] Load-time prediction from hotload-log.jsonl history
- [ ] Alerting: warn if planned load exceeds host VRAM budget

## 5. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Load takes longer than expected (4+ min for Q8) | Round delayed | Pre-warm: start loading when Orchestrator declares intent, before round starts |
| Idle gate never opens (stuck generation) | Deadlock | Timeout + wedge_force_recover.py fallback (proven 11-15) |
| VRAM fragmentation after multiple load/unload cycles | Load fails despite "enough" VRAM | nvidia-smi check before each load; full unload+reload if fragmented |
| Engine update kills all instances mid-swap | Total loss | Never schedule swap during engine updates; RecoverAll as safety net |
| Remote host unreachable during swap | Partial state | Per-host atomicity: if load fails, roll back that host only; other hosts unaffected |

## 6. Open Questions (for Orchestrator/human)
1. TTL for SLEEP state: 5 min default? Configurable per agent?
2. Should the portal auto-activate agents based on message @mentions, or always require explicit Orchestrator declaration?
3. Video/3D models: which specific models are in scope? (SDXL video? TripoSR? Meshy?) — affects VRAM planning
4. Priority ordering when VRAM is contested: is priority field sufficient, or do we need per-round overrides?
5. Should cold agents still appear in the group prompt (just unable to respond) or be fully hidden?

## 7. File Map (planned)
- memory/llm/hotload-plan.md (this file) — design + phases
- model_scheduler.py — core scheduler module (portal process)
- model_registry.json — fleet-level task model definitions
- agents.json — extended with model_spec per agent
- memory/llm/hotload-log.jsonl — append-only transition log
- /api/fleet/* endpoints in agent_portal.py
