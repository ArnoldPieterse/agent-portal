# Hotload Controller + Model Catalog - Built 2026-11-17
## What was built
- `hotload_controller.py` (root) - ops automation for on-demand model load/unload across fleet hosts
- `memory/llm/hotload-catalog.json` - model capability registry (3 active + 3 planned models, 3 agent profile templates)

## Commands verified (all pass in sandbox):
- `python hotload_controller.py status` -> reports all 4 hosts reachable/unreachable with error detail
- `python hotload_controller.py select --agent researcher` -> correctly maps to qwen3-27b-q4 (score 8.8, ACTIVE)
- `python hotload_controller.py select --capability video_generation` -> finds planned model (score 2.4, PLANNED)
- `python hotload_controller.py plan --agent orchestrator` -> full 5-step load plan with VRAM check
- `python hotload_controller.py plan --agent video_gen` -> correctly reports [BLOCKED] PLANNED + min VRAM requirement

## Architecture (for Orchestrator/Scribe coordination):
1. **Catalog** (hotload-catalog.json) = SSOT for model capabilities, VRAM needs, agent bindings
2. **Controller** (hotload_controller.py) = executes safe load/unload with idle gates, polling, alias verification
3. **Selector** (select command) = auto-matches task capability -> best model+host
4. **Planner** (plan command) = dry-run swap plan with risk assessment (eviction warnings, VRAM feasibility)

## Key design decisions:
- Wraps proven backend-swap procedure (memory/llm/backend-swap-procedure.md) - no new API calls invented
- Respects asymmetric eviction rule: Q4 131k ctx evicts Q8 (documented risk in plan output)
- Planned models scored at 0.3x availability multiplier so active models always rank higher
- VRAM feasibility check against host total prevents impossible plans
- Each execution writes timestamped JSON to memory/mechanic/hotload_results/

## What's needed next (for full productionization):
1. **Orchestrator**: integrate selector into agent onboarding flow - when a new task needs video/3D, call `select` then `plan` then `execute`
2. **Scribe**: add "on-demand agents" section to group management - track which specialized agents are active/inactive
3. **Model provisioning**: download video-gen + 3D model files to White (requires ~40GB disk space)
4. **agents.json extension**: add `activation: "on_demand"` field for non-persistent agents
5. **Portal integration**: /api/models/status endpoint that calls `hotload_controller.py status`

## Evidence artifacts:
- memory/mechanic/hotload_results/status_20261117_222103.json
- memory/mechanic/hotload_results/select_20261117_222121.json (video_generation)
- memory/mechanic/hotload_results/select_20261117_222122.json (researcher)
- memory/mechanic/hotload_results/plan_20261117_222143.json (video_gen - BLOCKED planned)
- memory/mechanic/hotload_results/plan_20261117_222144.json (orchestrator - full plan)

## Runbook note:
What broke: nothing new - this is greenfield infrastructure. The hotload controller wraps the proven 11-15 backend-swap procedure into a scriptable service. If load fails, check: (1) idle gate timeout = active generation blocking, (2) poll timeout = model too large for VRAM or disk I/O slow, (3) alias mismatch = folder was renamed after catalog entry was written.
