# Scribe - cycle-6 goals (set 2026-11-18; human directive: make hot LLM loading functional)

Supersedes cycle-5 (all closed; see memory/goals/scheduler.md). Headline per human:
**#1 = hot-LLM-loading functions, expanded + made FUNCTIONAL from prior design work.**

Prior art this builds on (do NOT reinvent):
- memory/llm/hotload-plan.md      - architecture + phases (PLANNED, not built)
- memory/llm/hotload-selector.md  - research + layer design (DRAFT)
- memory/llm/hotload-catalog.json v1.0 - model registry: hosts / models / planned_models / agent_profile_templates
- memory/llm/model_load_params.json    - PROVEN load bodies (atlas-q8, quinn-q4)
- memory/llm/backend-swap-procedure.md - PROVEN idle-gate -> load -> verify -> unload, zero-binding-loss
- memory/llm/studio-api.md       - :8888 endpoint map + reload recipe

State today: design + registry exist; swaps are still MANUAL one-shot schtasks. Nothing automated.
Cycle-6 = turn that into a working controller, then wire it to the portal.

1. **Functional Hotload Controller** - `python memory/scheduler/hotload.py <command>` reads
   hotload-catalog.json + model_load_params.json and drives Studio API :8888. Commands:
   - `plan --agents a,b,c`  -> DRY-RUN: which models resident vs need load, per-host VRAM fit,
     ordered load/unload sequence. No side effects.
   - `status`               -> per-host loaded models + aliases (GET /models + /api/settings/model-aliases).
   - `activate --agents a,b`-> idle-gate (poll active-generations==0) -> load missing models (proven
     bodies) -> poll until resident -> verify aliases unchanged -> report.
   - `deactivate --agents a`-> unload to free VRAM; poll loaded=false.
   Verified: plan+status run read-only against White :8888 with zero side effects; activate/deactivate
   round-trips on a scratch alias (load->resident->unload->gone) and appends memory/llm/hotload-log.jsonl;
   aliases identical before/after (zero binding loss).

2. **VRAM Fit Solver** - `plan` computes per-host feasibility from catalog vram_gb + nvidia-smi free,
   flags conflicts (e.g. Q8 30.1GB + Q4 23.7GB on one 32GB host = over budget).
   Verified: against the real catalog it reports White dual-resident FITS and a third 24GB model does NOT;
   output lists exact over/under by GB per host.

3. **Eviction Policy** - when target does not fit, pick lowest-priority resident to evict (priority from
   catalog), NEVER one with an active generation.
   Verified: unit tests cover 3 cases - fits->no eviction; needs-evict->evicts lowest-priority;
   active-gen present->refuses + reports which model is blocked.

4. **Transition Log + Load-Time ETA** - append every load/unload to memory/llm/hotload-log.jsonl
   {ts,host,agent,action,model,duration_s,vram_before,vram_after}; `eta --agents` predicts total load time
   from catalog load_time_s blended with observed history.
   Verified: log is valid JSONL after a real round; eta within +/-20% of measured on 3 samples.

5. **Portal Endpoints** - expose /api/fleet/status, /api/fleet/plan (dry-run), /api/fleet/activate,
   /api/fleet/deactivate in agent_portal.py wrapping hotload.py.
   Verified: each returns JSON; /api/fleet/status matches `hotload.py status`; /api/fleet/plan is side-effect-free.

6. **Catalog v2 + Registry Sync** - extend hotload-catalog.json with per-model priority + last-active ts,
   and a `sync` command reconciling catalog vs live /models (flags stale/missing entries).
   Verified: sync reports 0 drift on White after a fresh load; a planned model with no local folder is flagged not-loaded.

7. **Specialized-Model Slot Adapter (design->stub)** - define task_model schema (video/3D/large-context from
   catalog planned_models) + adapter interface so non-LLM runtimes (ComfyUI :8188) can be hotloaded; STUB only,
   no ComfyUI install this cycle.
   Verified: schema documented; a dry-run `plan` including one exclusive video model schedules full-GPU eviction first.

8. **Ops Runbook** - memory/llm/hotload-runbook.md: operator steps for manual fallback when the controller is
   down (reuse backend-swap-procedure.md), wedge recovery, rollback.
   Verified: runbook covers activate/deactivate/rollback/wedge with exact commands; cross-links procedure + recover_all.py.

9. **Safety Invariants Test** - harness asserting the hard rules from prior work: (a) load 200 ack != residency
   (must poll); (b) Q4 load EVICTS Q8 (asymmetric, per 11-15 drill finding); (c) aliases are path-bound (survive
   eviction); (d) never force-cancel an active generation.
   Verified: all 4 invariants asserted against recorded drill data (backend_swap_drill_result.json) and pass.

10. **Cycle-6 Synthesis + Handoff** - Scribe synthesis of the hotload build: decisions made, open questions
    (SLEEP TTL default? auto-activate trigger? which video/3D models in scope?), owner per next action; context
    handoff to Orchestrator/Mechanic for execution.
    Verified: memory/synthesis/hotload-cycle6.md written + handoff passes validate_handoff.py.

## Ownership & sequencing (Scribe schedules; others execute)
- #1,#2,#3,#4  -> Builder (code) + Mechanic (White :8888 access) ; Scribe verifies evidence
- #5           -> Builder (portal) 
- #6,#7        -> Scribe (registry/schema) + Mechanic (sync against live host)
- #8           -> Mechanic (runbook) + Scribe (review)
- #9           -> Verifier (invariants) 
- #10          -> Scribe
