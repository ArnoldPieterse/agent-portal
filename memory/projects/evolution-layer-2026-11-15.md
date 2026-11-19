# Evolution layer (generational selection over project changes) - 2026-11-15
Status: LIVE (CHG-0001 living gen 1; CHG-0002 candidate awaiting human selection).

## What it is
Human directive (rabbit/fox evolution video): evolve CHANGES to the project, not code directly.
Each change is an entity with a genome {kind, spec, params} on a target path. Selection = human
accept (survives) / reject or rollback (dies -> ⚠missing:graveyard.json autopsy). No fitness score.
Offspring of survivors are born as candidates via param jitter; never auto-applied.

## Where it lives
- evolution/README.md - ISLAND RULES, written before first birth (entity types: code_block/file/folder/project; pre-written tests mandatory at birth; wiring cost = size recorded; cap 25 living w/ cull; rescue <3)
- evolution.py (project root) - stdlib-only CLI engine: propose / accept / reject / breed / stats / autopsy / lineage / cull. EVOLUTION_HOME env override for scratch islands.
- evolution/population.json + evolution/graveyard.json - the population data.
## Current state (2026-11-15)
- CHG-0001 (project, "evolution layer scaffold") LIVING gen 1 - the island's first survivor is itself.
- CHG-0002 (code_block, "/api/evolution endpoints stats+accept/reject in agent_portal.py") CANDIDATE with 3 pre-written tests incl. restart-trap check. Awaiting human accept/reject; needs Builder + portal restart trap if accepted.

## Next steps
1. Human selects on CHG-0002 (accept -> Builder implements, Verifier runs the 3 pre-written tests).
2. Wire into round-table: Builder proposes candidates, Verifier runs pre-written tests before any accept ask.
3. Decision: expose evolution CLI as a tool in agents.json (Builder/Verifier lanes).

## Integrity
Engine smoke-tested on scratch island (propose/accept/breed/reject/stats/lineage/cull + no-test refusal) 2026-11-15. v1 mutation = numeric param jitter only; spec rephrasing left to the proposing agent (honesty clause in README).
