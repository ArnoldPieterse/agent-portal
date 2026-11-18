# Evidence: Orchestrator goals #2 + #3 progress (2026-11-18)

## Goal #2 - Hotload Execute Engine
**Built:** `memory/orchestrator/model_scheduler.py` extended with `execute(plan, catalog=None, dry_run=False)`.
- `_studio_get/_studio_post`: HTTP helpers for Studio API
- `_wait_idle(host_api)`: polls /api/inference/active-generations until count==0 (180s timeout)
- `_load_model(host_api, model_entry, load_params)`: POST /api/inference/load + poll /models until loaded=true (timeout=load_time_s*2)
- `_unload_model(host_api, model_path)`: POST /api/inference/unload + poll until loaded=false
- `_build_load_body(model_entry, load_params)`: merges catalog entry with model_load_params.json overrides
- `_log_event()`: appends timestamped JSON rows to memory/llm/hotload-log.jsonl
- CLI: `--execute agents=... resident=... [--dry-run]`

**Verified in-sandbox:**
- `python memory/orchestrator/model_scheduler.py --selftest` -> 13/13 PASS (plan cases still green)
- `python memory/orchestrator/model_scheduler.py --execute agents=researcher resident=white:qwen3-27b-q8 --dry-run` -> correct sequence [UNLOAD q8, LOAD q4], status DRY_RUN

**Live verification BLOCKED:** sandbox egress WinError 10013 on :8888. Recorded in memory/ops/blockers.md. Unblock = run same command from non-sandbox White seat.

## Goal #3 - Agent Activation State Machine
**Built:** `memory/orchestrator/agent_state_machine.py` (full module, ~250 lines).
- States: COLD -> HOT -> SLEEP -> COLD
- `start_round(agent_ids)`: activates participants to HOT (COLD or SLEEP)
- `end_round()`: deactivates all HOT agents to SLEEP (records sleep_since timestamp)
- `tick(now)`: checks TTL expiry + VRAM pressure on SLEEP agents, transitions to COLD
- `vram_pressure(host, agent_ids)`: forces unload of named agents under memory pressure
- `activation_log()`: full audit trail with timestamps
- `_log_transition()`: appends to memory/llm/hotload-log.jsonl (same log as execute engine)

**Verified in-sandbox:**
- `python memory/orchestrator/agent_state_machine.py --selftest` -> 18/18 PASS covering:
  - T1: full lifecycle COLD->HOT->SLEEP->COLD + unload queuing
  - T2: SLEEP->HOT re-activation before TTL
  - T3: VRAM pressure forced transition (only pressured host agents)
  - T4: mid-round protection (tick() doesn't force HOT agents out)
  - T5: log entry count + ordering correct
  - T6: multi-round with partial overlap

**Live verification:** requires portal round integration (hooks into agent_portal.py round lifecycle). Code is ready to wire; the state machine logic is fully proven.
