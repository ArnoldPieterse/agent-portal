# Run rules - read every run
Last updated: 2026-11-18. Parent: memory/INDEX.md (global pointer map). Sibling rule docs: memory/portal/file-modularity.md, memory/goals/INDEX.md. Attached to the global index so every agent prompt carries it - keep under ~1500 chars.

## Standing rules
1. Scheduled goals run in the background. If a goal's closure is gated by a future date or recurring cadence (weekly/monthly/daily, multi-day data windows), move it to memory/goals/scheduled-background.md and leave its numbered pointer line in the agent file. Such goals must never block, gate, or hold up main-goal progress; they are checked on their own schedule.
2. Main goal files (memory/goals/<agent>.md) hold only goals completable within the current cycle/run window.
3. Close goals only with verified evidence: mark "Verified: <evidence>" citing file/commit/log lines. No closure without evidence.
4. Files stay modular: one concern per file, header pointer block, small size budgets -> memory/portal/file-modularity.md. Pointers beat copies.
5. MEMORY.md is a HOT FILE ONLY (state line + counter + notes); details go to leaves with pointers from indexes.
6. Commit after each completed goal batch; TODO.md status lines newest at top.
