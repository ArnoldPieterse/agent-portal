# Supersession-chain integrity run — 2026-11-16 18:22 (Scribe #5, policy owner)

Parent: memory/scribe/INDEX.md · Validator: memory/scribe/supersession_check.py · Raw: memory/scribe/supersession-report.json

## Verdict (fresh measurement, timestamp 2026-11-16T18:22:10)
- Scanned 521 leaves, 77 supersession edges.
- **cycles_detected = 0** — no circular SUPERSEDED chains; canonical head per topic is unambiguous. (core integrity property HOLDS)
- broken_chains = 55 — a SUPERSEDED leaf whose successor pointer is missing/unresolvable. Enforcement backlog to reduce.
- orphaned_superseded = 10 — files marked superseded with NO successor edge at all (worst class; list in report `orphaned_superseded`).
- canonical_heads = 57.

## Acceptance-test status for goal #5
Test: "cycle-2 weekly runs with zero unresolved heads." Cycle-detection half is GREEN (0 cycles, unambiguous heads). The broken-chain/orphan backlog (55/10) is the open reduction target — NOT yet at zero, so this run is recorded as a WEEKLY RUN + report (the standing deliverable), not a full pass.

## Top orphaned-superseded targets (fix = add successor pointer or un-mark)
- memory/goals.md, memory/goals/archive/README.md, memory/goals/archive/2026-11-13-agent-goals-SUPERSEDED-partial.md
- memory/archivist/MEMORY.md, memory/researcher/MEMORY.md (agent hot-files marked superseded — likely false SUPERSEDED tags)
- memory/designer/files-panel-patch.md, memory/builder/index-repin-r65-v21-2026-11-14.md

## Next action (owner: Scribe, assist: Archivist#5)
Resolve the 10 orphaned-superseded first (cheapest, highest signal); re-run supersession_check.py; target broken_chains < 55 next weekly run.
