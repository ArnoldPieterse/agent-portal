# Auto-LLM Selector & Hotload Architecture (Research + Proposal)
Last updated: 2026-11-17. Status: RESEARCH COMPLETE, DESIGN DRAFT.
Parent: memory/llm/INDEX.md | Siblings: instances.md, backend-swap-procedure.md, studio-api.md

## Problem Statement
Current fleet runs 8 agents on 2 GPU slots (dual residency Q4+Q8) with global serialization
(parallel_slots=1). Adding specialized models (video gen, 3D env, large-context reasoning) requires:
1. A ROUTER that decides WHICH model a task needs
2. A HOTLOAD mechanism that swaps models in/out of GPU memory on demand
3. An AGENT PROFILE system that binds model capabilities to agent roles dynamically
4. LOAD MANAGEMENT so Scribe/Orchestrator control activation (not all agents always live)

## Research Findings (2025-2026 state of the art)

### 1. SwapServeLLM (Oxford, SC'25 workshop)
- Engine-agnostic hot-swapping using GPU checkpointing (NVIDIA driver feature)
- Architecture: OpenAI-compatible router -> request handler -> model workers -> scheduler -> task manager -> engine controller
- Key insight: demand-aware preemption selects which loaded model to evict based on concurrent request patterns
- Memory reservation with priority queue; swap-in/swap-out is transparent to the client
- Source: https://github.com/rst0git/SwapServeLLM, paper at dl.acm.org/doi/10.1145/3731599.3767354

### 2. vLLM Semantic Router (Apache 2.0, 2025-2026)
- Programmable decision layer: "select or combine models through explicit policy"
- Signal-driven routing: intent, difficulty, context length, modality, risk, runtime observations
- Supports escalation (small model -> larger), multi-model workflows, route behavior (RAG, caching, safety)
- OpenAI/Anthropic-compatible endpoint; agent harness unchanged
- Source: https://vllm-sr.ai/docs/intro/

### 3. LLMRouter (arXiv 2608.06867, Aug 2026)
- Unified formulation of LLM routing as sequential decision process
- Five components: context, candidate set, scoring function, selection policy, execution
- Enables fair comparison and extension across router implementations
- Source: https://arxiv.org/abs/2608.06867

### 4. Microsoft Foundry Model Router (Azure, 2025-11 release)
- Per-turn model selection: cheap for trivial turns, reasoning-grade for multi-step
- Tool-use support; integrates into agent service natively
- Cost-aware: scores candidates on quality/latency/cost per request
- Source: learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-router-how-it-works

### 5. Local Video/3D Generation (for hotload targets)
- Wan2.1 (Alibaba): text-to-video, image-to-video; runs via ComfyUI; needs ~12-24 GB VRAM
- SVD (Stable Video Diffusion): shorter clips, lower VRAM (~8-12 GB)
- 3D: TripoSR / InstantMesh for 3D from text/image; Hunyuan3D for full pipeline
- These are DIFFERENT runtimes (diffusion, not LLM) - need adapter layer in the hotload system
- Source: github.com/lilinsong1/comfyui-wan-video-pipeline, build.nvidia.com/station/comfyui

## Proposed Architecture (Fleet-Specific)

### Layer 0: Model Registry (new file: memory/llm/model_registry.json)
```json
{
  "models": [
    {
      "id": "qwen3-27b-q8",
      "path": "C:\\Users\\White\\.lmstudio\\models\\lmstudio-community\\Qwen3.8-27B-Q8_0",
      "type": "llm",
      "quant": "Q8_0",
      "vram_gb": 30.1,
      "max_context": 32768,
      "capabilities": ["code", "reasoning", "long_doc"],
      "load_time_s": 240,
      "host": "white"
    },
    {
      "id": "wan21-t2v",
      "path": "C:\\Users\\White\\.comfyui\\models\\checkpoints\\wan2.1-t2v-14B.safetensors",
      "type": "video_gen",
      "runtime": "comfyui",
      "vram_gb": 24,
      "max_context": null,
      "capabilities": ["text_to_video", "image_to_video"],
      "load_time_s": 180,
      "host": "white"
    }
  ],
  "agent_bindings": {
    "orchestrator": {"primary": "qwen3-27b-q8", "fallback": "qwen3-27b-q4"},
    "video_gen": {"primary": "wan21-t2v", "runtime": "comfyui"}
  }
}
```

### Layer 1: Router (new module: llm_router.py)
- Input: task description + agent profile + available GPU memory
- Output: model_id to load (or "already loaded")
- Decision signals (borrowed from vLLM Semantic Router):
  - Task modality: text / image / video / 3D
  - Context length needed vs model max_context
  - VRAM budget: nvidia-smi free memory per GPU
  - Agent capability tags from agents.json
- Scoring: weighted (capability_match * 0.5 + vram_fit * 0.3 + load_time_penalty * 0.2)
- Policy: if best model not loaded -> trigger hotload; if VRAM insufficient -> evict lowest-priority resident

### Layer 2: Hotload Engine (extends backend-swap-procedure.md)
Current procedure is MANUAL + one-shot schtask. Upgrade to:
1. **Idle gate** (existing): poll /api/inference/active-generations until count==0
2. **VRAM check**: nvidia-smi --query-gpu=memory.free --format=csv
3. **Eviction policy** (NEW): if target model doesn't fit, unload lowest-priority resident
   - Priority = agent activity recency (from portal round logs)
   - Never evict a model with an active generation
4. **Load**: POST /api/inference/load (existing endpoint, proven bodies in backend-swap-procedure.md)
5. **Non-LLM runtimes** (NEW): for video/3D models, spawn ComfyUI subprocess instead of Studio API
   - Adapter: `comfyui_adapter.py` wraps ComfyUI HTTP API (:8188) as an OpenAI-compatible endpoint
6. **Poll + verify**: GET /models until loaded=true; for non-LLM, poll ComfyUI /system_stats
7. **Bind**: update agents.json model_id for the requesting agent (or create new ephemeral profile)
8. **Unload on TTL**: after task completes + idle_timeout (default 300s), unload to free VRAM

### Layer 3: Agent Activation Manager (new module: agent_activation.py)
- NOT all agents are always in the group chat
- Scribe/Orchestrator control which agents are "active" per round
- Active agents get their model loaded; inactive agents' models can be evicted
- State machine per agent: DORMANT -> LOADING -> ACTIVE -> COOLDOWN -> DORMANT
- API: POST /api/agents/{id}/activate {model_id, ttl_s} / POST /api/agents/{id}/deactivate
- Integration: portal round dispatcher checks activation state before adding agent to group

### Layer 4: Load Balancer (future, multi-host)
- When Red/Pale/Black hosts come online, distribute models across them
- Router gains a host-affinity signal: prefer local model if available
- Fallback: remote API call (existing pattern from memory/llm/hosts.md)

## Implementation Phases
| Phase | Scope | Effort | Dependency |
|-------|-------|--------|------------|
| P1 | Model registry + router scoring (text-only, existing models) | 2h | None |
| P2 | Hotload engine automation (replace manual schtask with API-driven loop) | 3h | P1 |
| P3 | Agent activation manager (Scribe/Orchestrator control) | 2h | P2 |
| P4 | Non-LLM adapter (ComfyUI video gen as hotload target) | 4h | P2 + ComfyUI install |
| P5 | Multi-host load balancer | 3h | P3 + remote hosts online |

## Gaps & Risks
- [ ] Studio API serializes globally (parallel_slots=1) - hotload won't help if only one model can generate at a time. Fix requires Studio-side change OR separate llama-server per model.
- [ ] Video/3D models need DIFFERENT runtimes (ComfyUI, not llama.cpp) - adapter layer is non-trivial
- [ ] VRAM math: Q8_0 (30GB) + Wan2.1 (24GB) = 54GB > single GPU (24GB). Must be sequential, not concurrent.
- [ ] Load times are 3-4 min for LLMs - router should pre-warm if it predicts a model switch
- [ ] agents.json is currently static; dynamic binding needs either file rewrite per round OR in-memory override layer

## Source Index
- SwapServeLLM: github.com/rst0git/SwapServeLLM (code + paper)
- vLLM Semantic Router: vllm-sr.ai/docs/intro/
- LLMRouter paper: arxiv.org/abs/2608.06867
- Microsoft Model Router: learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-router-how-it-works
- Wan2.1 ComfyUI: github.com/lilinsong1/comfyui-wan-video-pipeline
- Fleet current state: memory/llm/instances.md, backend-swap-procedure.md, studio-api.md