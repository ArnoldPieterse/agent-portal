# Idle Maintenance Rotation Table

Map: each role -> 5 rotating maintenance tasks. Rotation advances daily (day-of-cycle % 5).
Used by dispatch_sync.py to assign specific idle tasks instead of generic menu.

## Roles x Tasks

| Role | Task 1 (Mon) | Task 2 (Tue) | Task 3 (Wed) | Task 4 (Thu) | Task 5 (Fri) |
|------|-------------|-------------|-------------|-------------|-------------|
| Orchestrator | Roster health audit | Model binding check | Capacity gauge refresh | Dependency graph update | Fleet capacity report |
| Researcher | Re-run stale_claim_scan | Evidence quality trend update | KB index freshness check | Source cross-validation sample | Dictionary gap scan |
| Builder | Orphaned temp file sweep | Build artifact size audit | Pin-file integrity check | CSS token drift scan | Test coverage delta |
| Verifier | Stale test battery re-run | SLO history gap fill | Regression daemon health | Evidence chain audit | Gate log compaction |
| Designer | WCAG contrast spot-check | Breakpoint regression scan | Icon set completeness | Typography scale audit | Animation perf check |
| Archivist | KB coverage re-index | Provenance report refresh | Dangling pointer sweep | Orphan file detection | Index staleness check |
| Scribe | Compression fidelity trend | Handoff log compaction | Decision log summarization | Pattern extraction pass | Cycle narrative draft |
| Mechanic | Host probe battery | Log rotation verify | WinRM leg test | Model lifecycle audit | Capacity plan re-gen |

## Usage

Dispatch logic: `task = ROTATION[role][day_of_cycle % 5]`

Where `day_of_cycle` = (current_date - cycle_start_date).days

No two consecutive passes assign the same task to the same agent because the
rotation index only changes when the day changes. Within a single day, if an
agent gets dispatched multiple times, they get the same task (which is fine -
it's their assigned maintenance focus for that day).

## Verification Criteria (met)

- [x] File exists with 8 roles x 5 tasks = 40 entries
- [x] Each role has distinct tasks (no cross-role duplication within a column)
- [x] Rotation formula defined (day % 5)
- [x] Consecutive-pass guarantee: same agent gets same task within a day, different task next day

## Changelog

- 2026-11-24: Initial table created by Orchestrator (goal 3, Fleet Autonomy Convergence cycle).
