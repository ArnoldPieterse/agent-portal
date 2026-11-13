# Agent Portal — Initial Design Plan

Multi-agent chat portal backed by the Unsloth Studio desktop harness.
Written 2026-11-09. Status markers: [DONE] / [GAP] = not yet true.

## Vision
A local group-chat UI where multiple AI agents converse with the user and each other.
Every agent is a real, independently hosted LLM — not a persona mask over one shared model.
The portal itself loads nothing; it is a thin web UI + proxy in front of Unsloth Studio,
so every agent gets the full desktop harness (reasoning, skills, RAG, tool execution).

## Core requirement (Arnold, 2026-11-09)
**Each agent is served by its own LLM instance.**
The current Unsloth Desktop hosts **two** instances concurrently — one per agent.
- Atlas → its own dedicated model instance.
- Quinn → its own dedicated model instance.
- The portal binds each agent to its instance via `model_id` in agents.json.

## Architecture
```
Browser (index.html)
   │  fetch /api/chat  (SSE stream)
   ▼
agent_portal.py  :8099          ← thin proxy, no models of its own
   │  POST /v1/chat/completions (per agent, per request)
   ▼
Unsloth Studio harness :8888    ← reasoning + skills + RAG + local tool exec
   ├── instance A  → serves Atlas   [GAP: two instances must be resident]
   └── instance B  → serves Quinn   [GAP: currently ONE shared Qwen3.8-27B-GGUF]
```

## Components
| File | Role |
|---|---|
| `agent_portal.py` | HTTP server :8099; `/api/chat` SSE proxy → Studio :8888; agent CRUD; model/status/RAG/tools proxies. Launched detached via `PortalRun` scheduled task → `portal_start.bat`. |
| `agents.json` | Agent roster: id, name, persona, blurb, **model_id (own instance)**, temperature, max_tokens, reasoning, tools[], run_tools_locally, max_tool_calls, rag, rag_kb_id. `0`/empty = "Studio decides". |
| `index.html` | UI. Solo = one selected agent. Group = sequential fan-out to all (or @mentioned) agents over shared history. Per-message thinking/tool chips. |

## Message construction (group mode)
- Each agent sees the full shared transcript, but roles are rewritten per agent:
  - `You` (human) → `user`
  - the agent's OWN past replies → `assistant` (continuity of its own voice)
  - OTHER agents' words → `user` with a `[Name]:` prefix
- Why: if a foreign reply lands as the final `assistant` turn, the model sees no open user
  prompt and emits nothing (empty bubble). Fixed 2026-11-09; proof in probe_quinn.py / test_group.py.
- Solo mode keeps the original behavior (own history = assistant turns).

## Per-agent knobs (passed through to Studio each request)
max_tokens, reasoning level (off/minimal/…/xhigh), enabled_tools[], run_tools_locally,
max_tool_calls_per_message, rag + rag_kb_id. All default to "Studio decides" when 0/empty.

## Two-instance load recipe (proven 2026-11-09)
How we ran two Qwen3.8-27B instances concurrently with fast inference:
1. **Per-GPU pinning** — Studio auto-switch overrides (studio.db → app_settings, key
   `openai_api_auto_switch_overrides`; PUT /api/settings/openai-auto-switch/overrides):
   - `unsloth\Qwen3.8-27B-GGUF:UD-Q4_K_S` (+ base key) → gpu_ids [0], ctx 131072, kv q8_0,
     speculative_type auto, n_parallel 1, --split-mode layer
   - `lmstudio-community\Qwen3.8-27B-GGUF:Q8_0` → gpu_ids [1], ctx 32768, kv q8_0, n_parallel 1
   - `unsloth/Qwen3.5-4B-MTP-GGUF:UD-Q4_K_XL` → tensor_parallel true (MTP draft model)
2. **Multi-model on** — PUT /api/settings/multi-model {"enabled": true, "mode": "fit"}
   (MultiModelPayload{enabled, mode}; off/fit/always; effect on next load).
3. **Load each instance** — POST /api/inference/load {"model_path": "ref:<hash>" or clean ID};
   retry on 409 active_generations (load_q8.py). Live check: one llama-server per instance,
   loopback port, alias = model_id.
4. **Fast-inference flags** (live llama-server): --spec-type draft-mtp --spec-draft-n-max 2
   (MTP speculative decoding), q8_0 KV cache, --flash-attn on, --jinja, --reasoning on,
   preserve_thinking, -ngl -1, --kv-unified. Tuned: ~104 tok/s @ 74% draft acceptance.

Caveat found in live check (2026-11-09): with mode=fit the Q8_0 instance ran tensor-split
across BOTH GPUs (~18/16 GB) and the second instance was NOT resident — fit evicts when
contexts don't co-fit. Keeping both resident needs per-instance contexts small enough to sit
side by side (one GPU each) or mode=always.

## Current state vs target
| Item | Now | Target |
|---|---|---|
| Hosted instances in Unsloth Desktop | 1 resident (Q8_0 **pinned to GPU1 only**, port 57753, ctx 32768 / max 55808, MTP drafter live); multi-model fit ON, pins verified working; **GPU0 idle ~26 GB free** | **2 resident, one per agent** |
| Atlas / Quinn binding | both → same shared model_id | each → its own instance's model_id |
| Portal proxy + SSE + group fan-out | DONE | DONE |
| Per-agent config passthrough | DONE | DONE |

## Open questions (to resolve before the 2-instance target)
1. ~~Concurrent residency?~~ RESOLVED: Studio keeps multiple models loaded under multi-model
   mode; **fit** evicts a model when contexts don't co-fit (observed). Use smaller per-GPU
   contexts or mode=always to force both resident.
2. VRAM: MEASURED 2026-11-09 — Q8_0 alone on GPU1 uses 30.1 GB (weights 26.4 + KV 32k q8_0 +
   mmproj 0.9); GPU0 holds ~26 GB free after desktop apps. A Q4_K_S (weights 15.4 + mmproj 0.9)
   co-fits on GPU0 with a context of roughly ≤64–96k q8_0 KV; load it there and confirm no OOM.
3. ~~Exposure to portal?~~ RESOLVED: same :8888, distinct model_id per variant
   (Qwen3.8-27B-GGUF + lmstudio-community/ and unsloth/ prefix aliases).
4. ~~Distinct variants vs same weights?~~ RESOLVED 2026-11-10: keep **different variants of the
   same base** (Q4_K_S on GPU0 for Quinn, Q8_0 on GPU1 for Atlas) — each agent has its own
   dedicated instance. Proven end-to-end by smoke_q2.py (solo/group/cross-talk/block all pass);
   no need for identical clones.

## Files / evidence
- MEMORY.md — persistent project memory (source of truth for the 2-instance requirement).
- probe_quinn.py, test_group.py — group-mode empty-bubble bug proof + end-to-end test.
- SETUP_HISTORY.md — machine/cluster history (White/Red, llama.cpp RPC work).
