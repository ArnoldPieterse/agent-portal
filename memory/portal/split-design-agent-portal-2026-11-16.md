# agent_portal.py split design (2026-11-16, Archivist)

Parent: memory/portal/INDEX.md. Sibling: file-modularity.md (the rule this follows).
Consumer: Builder (implements the split). Constraint: PortalRun task runs `python agent_portal.py` - entry point must stay.

## Strategy

Extract functions into `portal_modules/` package. `agent_portal.py` becomes:
1. Constants block (PORT, STUDIO, HERE, file paths, regexes) ~100 lines
2. `from portal_modules import *` (or explicit imports)
3. Handler class (unchanged, references module functions by name)
4. `if __name__ == "__main__": main()`

No circular imports: modules only depend on constants from the top level.
To avoid import-order issues, put shared constants in `portal_modules/constants.py` and have both `agent_portal.py` and each module import from there.

## Module map (9 files + entry)

| File | Lines | ~KB | Functions |
|------|-------|-----|-----------|
| portal_modules/constants.py | ~100 | 4 | PORT, STUDIO, HERE, all *_FILE paths, UMQ_MAX, HIST_MAX, _MEMORY_TEMPLATE, _STATE_RE, LOCAL_TOOLS, REASONING_LEVELS, XTALK_LIMIT, RESET_PHRASE |
| portal_modules/studio_client.py | ~143 | 6 | studio_base, studio_headers, _model_load_status, rag_base, rag_headers, studio_post, scan_remote_models, _fleet_probe |
| portal_modules/workspace.py | ~308 | 13 | _find_sandbox_dir, _git_allowlist, _same_file, _sync_workspace_to_sandbox, _auto_commit, _merge_queue_scan, _merge_queue_status, _restore_merge_queue, _safe_upload_path, _safe_session |
| portal_modules/agents.py | ~200 | 9 | load_activity, _act_log, _tool_names, _norm_tools, default_agent_fields, apply_agent_fields, load_agents, save_agents, get_agent |
| portal_modules/prompts.py | ~192 | 8 | build_system_prompt, parse_dm_segments, render_dm_view, to_openai_messages |
| portal_modules/memory_state.py | ~523 | 23 | _umq_*, _load_history, _save_history, _load_run_state, _save_run_state, load_memory, _write_memory, _read_state_unlocked, _reset_counter, _bump_counter, _shared_memory_block, _index_block, _live_plan_block, _ack_nudge, _safe_memory_file, _safe_workspace_file, _aux_chat, _mem_lookup_round, _mem_store_round, _hot_notes_block, _append_hot_note, _group_round_summary |
| portal_modules/chat_stream.py | ~275 | 12 | stream_chat, _effective_reply, _finish_chat, _perf_record, _percentile, _perf_snapshot |
| portal_modules/group_run.py | ~461 | 20 | _RunStopped, _FrameSink, _load_group_run, _save_group_run, _append_history, _run_event, run_turn_captured, _parallel_turns, _group_run_worker, start_group_run |
| portal_modules/goals_ops.py | ~534 | 23 | _agent_goals_block, _stall_killer, _auto_resume_watchdog, _reap_stale_group_run, _prune_run_journals, _clear_stale_busy, _ops_snapshot, _goals_snapshot, _fleet_health_snapshot, _decisions_snapshot, _reached_at_commit, _goals_history, _evolution_mod, _netcmd_mod, _goal_ledger_mod, _evolution_snapshot, _run_index_check, _prune_todo, _git, _git_status |
| agent_portal.py (entry) | ~800 | 34 | constants re-export + Handler class + main() |

Total: ~2740 lines in modules + ~800 entry = ~3540 (vs current 3734; difference = dedup of shared imports).

## Implementation order (smallest risk first)

1. **constants.py** - pure data, zero logic. Extract all module-level constants.
2. **studio_client.py** - leaf dependency (only needs constants). No other module calls into it except chat_stream + prompts.
3. **workspace.py** - depends on constants only. Called by Handler for /api/merge-queue routes.
4. **agents.py** - depends on constants. Called by Handler + prompts.
5. **prompts.py** - depends on agents, memory_state (for _index_block etc). Called by chat_stream.
6. **memory_state.py** - depends on constants + studio_client (_aux_chat). The largest module; if it exceeds 40 KB after extraction, split into memory_state.py + umq.py (the _umq_* cluster is self-contained).
7. **chat_stream.py** - depends on studio_client, prompts, memory_state. Called by group_run.
8. **group_run.py** - depends on chat_stream, agents, memory_state. The most complex module (threading, stop events).
9. **goals_ops.py** - depends on constants + workspace (_git). Mostly self-contained snapshot functions.
10. **agent_portal.py** - trim to entry: import from modules, keep Handler class + main().

## Verification checklist (for Verifier)

- [ ] `python agent_portal.py` starts portal on :8099 (PortalRun task unchanged)
- [ ] GET /api/goals returns correct JSON (same schema as pre-split)
- [ ] GET /api/health/fleet returns all 4 hosts
- [ ] POST /api/chat group mode: one full turn completes with frames
- [ ] GET /ui/app.css still 200 (static route unaffected)
- [ ] `python -c "import portal_modules"` succeeds from the project dir
- [ ] No circular import warnings in stderr on startup
- [ ] Each module file has header pointer block (per file-modularity.md rule 2)

## Risk notes

- **Threading**: group_run.py uses ThreadPoolExecutor + threading.Event. Moving these to a separate module is safe as long as the Handler's do_POST still calls `start_group_run()` by name.
- **Global state**: Several functions read/write JSON files (agents.json, memory.md, run_state.json). These are file-based, not in-memory globals, so module boundaries don't create shared-state issues.
- **Handler references**: The Handler class calls ~40 module functions. After split, these become cross-module imports. Python resolves them at call time, so no forward-reference issues as long as all modules are imported before the server starts (which they will be via `from portal_modules import *` in agent_portal.py).
- **_git() function**: Used by goals_ops AND workspace. Put it in workspace.py (it's a git utility) and have goals_ops import from there.

## Pointers
- File-modularity rule: memory/portal/file-modularity.md
- Restart procedure: memory/ops/windows-runbook.md
- Current file inventory: memory/portal/INDEX.md