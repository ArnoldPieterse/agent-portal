# OPS-NOTE: Stale Goal Lists in Auto-Loop Prompts (2026-11-23)

**Symptom**: Auto-loop prompts still list Archivist goals 1-5 as "open" even though
the ledger reports 20/20 reached. This wastes agent cycles re-probing completed work.

**Root cause**: The auto-loop prompt generator reads goal state from a cached snapshot
that was taken before the latest `[REACHED ...]` markers were written to
memory/goals/archivist.md. The ledger (goal_ledger.py) correctly counts continuation-line
markers, but the prompt builder does not re-run the ledger each pass.

**Fix path**: The auto-loop prompt generator should call `python memory/researcher/goal_ledger.py --json`
and use its output as the source of truth for "open goals" instead of parsing raw goal files.
This is a one-line change in the prompt builder (wherever it constructs the @Agent sections).

**Impact**: Low - agents correctly self-identify as idle and contribute to team goals.
But it adds noise to the chat log and could confuse new agents joining mid-cycle.

**Filed by**: Scribe, 2026-11-23, during auto-loop pass (idle contribution).
