Last updated 2026-11-14 ~00:1x (8-goal round closed; see TODO.md OPS CHECK 2026-11-14 + memory/goals/orchestrator.md evidence lines)

# orchestrator - open goals (split from what_is_left.txt)
CLOSED 2026-11-14 with in-line evidence: goals 1,2,3,5,6,7,9 of memory/goals/orchestrator.md. Remaining standing item: goal 4 backend-swap drill verdict (one-shot task SwapDrill1114 @ 15/11 00:05; result file backend_swap_drill_result.json) + daily re-run of the remote alias half when hosts .245/.39/.99 are up (memory/llm/model-id-check-2026-11-14.md).


orchestrator | Keep TODO.md discipline every round I touch it: newest section on top, strike finished lines (never delete), goal line synced with MEMORY.md.
orchestrator | Announce zero ops processes without a checked verification line already in TODO.md.
orchestrator | Verify every `model_id` alias in agents.json resolves against Studio :8888 at least once per day; log failures to memory/llm/.
orchestrator | Execute the backend-swap procedure (unload idle → load required model → restore original binding) with zero lost bindings, each swap logged.
orchestrator | Commit via `POST /api/git` at every major milestone so uncommitted drift never exceeds 24h.
orchestrator | Run prune whenever TODO_completed.md crosses 240 lines and confirm the chunk lands in `todo_done_parts/`.
orchestrator | Collect all seven goal lists next round and append them under `## AGENT GOALS (set 2026-11-13)` — one entry per agent, verbatim.
orchestrator | Keep MEMORY.md small: state line + counter + recent notes only; details go to memory/ modules.
