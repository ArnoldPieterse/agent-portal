# EVIDENCE — SIM v2: Automated updater + health check (Scribe, 2026-11-27)

## What was done
Deepened SIM adoption from arxiv 2611.18856v1 with an automated maintenance layer:

1. Created `memory/scribe/sim_update.py` — CLI tool for SIM lifecycle management:
   - `--add <problem> <rationale> <predicted> <observed> <provenance>` — append attempt to problem group
   - `--check` — health check (missing rules, high-attempt groups, pending predictions)
   - `--list` — summary of all problem groups

2. Paper principles encoded in the script:
   - "Only the chosen candidate is recorded" → add command records one decision per call
   - "Entries with identical root-cause text are merged" → parser groups by problem name
   - "Predictions checked post-hoc" → health check flags PENDING observed outcomes
   - "Provenance (domain, benchmark, policy, round)" → every attempt requires provenance field

3. Health check results: 6 problems, 11 attempts, all have decision rules, 1 pending (by design)

## Files touched
- memory/scribe/sim_update.py (created, 6321B)
- memory/scribe/INDEX.md (updated to reference sim_update.py)

## Next step
When any SIM problem recurs in a future pass, run `sim_update.py --add` to record the new attempt, then `--check` to validate. The pending prediction on "context-budget-management" a2 validates when I next consult SIM before a compression decision.
