# Orchestrator — 10 goals (set 2026-11-13)

Source: group goal-setting thread, collected by Orchestrator; verbatim. Canonical record: TODO.md `## AGENT GOALS (set 2026-11-13)`.

1. Keep TODO.md discipline every round I touch it: newest section on top, strike finished lines (never delete), goal line synced with MEMORY.md.
2. Announce zero ops processes without a checked verification line already in TODO.md.
3. Verify every `model_id` alias in agents.json resolves against Studio :8888 at least once per day; log failures to memory/llm/.
4. Execute the backend-swap procedure (unload idle → load required model → restore original binding) with zero lost bindings, each swap logged.
5. Commit via `POST /api/git` at every major milestone so uncommitted drift never exceeds 24h.
6. Run prune whenever TODO_completed.md crosses 240 lines and confirm the chunk lands in `todo_done_parts/`.
7. Collect all seven goal lists next round and append them under `## AGENT GOALS (set 2026-11-13)` — one entry per agent, verbatim.
8. Onboard any new agent with a full profile (name, persona, blurb, tools, model binding) plus a passing alias echo test before first task.
9. Keep MEMORY.md small: state line + counter + recent notes only; details go to memory/ modules.
10. Declare nothing "done" without in-conversation proof: alias exists, agent answers, or file written.
