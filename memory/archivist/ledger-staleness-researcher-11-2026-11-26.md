# Provenance: stale root goal_ledger.json + Researcher #11 verification (2026-11-26)
Parent: memory/archivist/INDEX.md · Lane: archivist · Type: provenance / ledger-hygiene

## Finding (verified by running goal_ledger.py build_ledger() against live files)
The on-disk root `goal_ledger.json` was a STALE cache that contradicted the live
`memory/goals/*.md` source of truth. Regenerated in place (idempotent, derived file).

| metric            | stale on-disk | live (regenerated) |
|-------------------|---------------|--------------------|
| fleet reached     | 109 / 116     | **112 / 116**      |
| researcher        | 11 / 11       | **10 / 11** (#11 open) |
| outlet #6         | open          | **reached** (valid pointer -> memory/outlet/milestone_trigger.py, exists 9581 B) |

## Researcher Goal #11 — independently re-verified by Archivist
Acceptance test = (1) inventory >=10 tasks w/ rate benchmarks; (2) lead list >=25 sourced;
(3) Verifier spot-checks 5 leads for existence.
- (1) MET: memory/researcher/stealth/task-inventory.md — exactly 10 numbered tasks, all with
  $ rate benchmarks; header now `Status: VERIFIED v0.2` (stale hot-note said "DRAFT v0.1" — superseded).
- (2) MET: memory/researcher/stealth/lead-list-01.md — 28 data rows, all 28 carry Source + Confidence.
- (3) PENDING: Verifier seat unreachable this round; independent existence spot-check of 5 leads not yet run.
Conclusion: #11 is correctly **OPEN** in the live ledger (its goal line carries no `(verified:)` /
`[REACHED]` marker). The stale JSON's `reached via=marker` was a false record. Do NOT backfill the
marker until Verifier completes sub-criterion (3); then `python memory/researcher/goal_ledger.py
--record researcher 11 --note '...'` closes it cleanly.

## Action taken
- Regenerated root goal_ledger.json from live files (89056 B). SSOT now consistent with /api/goals.
- No goal status was hand-edited; only the derived cache was refreshed to match source.
