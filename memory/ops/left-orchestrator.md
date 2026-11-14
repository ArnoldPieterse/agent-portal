Last updated 2026-11-13

# orchestrator - open goals (split from what_is_left.txt)

orchestrator | Keep TODO.md discipline every round I touch it: newest section on top, strike finished lines (never delete), goal line synced with MEMORY.md.
orchestrator | Announce zero ops processes without a checked verification line already in TODO.md.
orchestrator | Verify every `model_id` alias in agents.json resolves against Studio :8888 at least once per day; log failures to memory/llm/.
orchestrator | Execute the backend-swap procedure (unload idle → load required model → restore original binding) with zero lost bindings, each swap logged.
orchestrator | Commit via `POST /api/git` at every major milestone so uncommitted drift never exceeds 24h.
orchestrator | Run prune whenever TODO_completed.md crosses 240 lines and confirm the chunk lands in `todo_done_parts/`.
orchestrator | Collect all seven goal lists next round and append them under `## AGENT GOALS (set 2026-11-13)` — one entry per agent, verbatim.
orchestrator | Keep MEMORY.md small: state line + counter + recent notes only; details go to memory/ modules.
