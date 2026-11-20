# Researcher — 5 UNCITED→REAL ledger closures (2026-11-20, auto-loop option c)

Parent: memory/researcher/INDEX.md. Scope: evidence-ledger upkeep only; no live :8888 probe, egress wall NOT re-probed.

## What verify_claims.py reported (before)
`70 REAL / 0 PHANTOM / 10 UNCITED`. All 10 UNCITED were genuine landed work whose goal-block prose cited an artifact path that PATH_RE (`memory/[A-Za-z0-9_./-]+\.(?:py|md|jsonl|json)`) could not match — either the `memory/` prefix was missing or the string was truncated before its `.md` extension.

## Method (skeptical, per-claim)
1. Ran `python memory/ops/verify_claims.py` fresh → captured the 10 UNCITED.
2. For each, located the real on-disk artifact; confirmed it is NOT a stub: `py_compile` PASS on scripts + read the dated report/complete-note content to confirm it matches the claim.
3. Added exactly ONE machine-checkable pointer line (a full `memory/...md` path) to that goal block so PATH_RE can verify it against disk. No marker downgraded; no work re-asserted beyond what the artifact shows.

## The 5 closed (all verified on this seat)
| goal | cited artifact (exists, size) | content check |
|---|---|---|
| mechanic #8 Capacity Planning Report | memory/mechanic/capacity-report-2026-11-20.md (2126B) | real 4-section report disk/VRAM/network/predictions, all 4 hosts; capacity_report.py compiles |
| archivist #6 Archive Compaction | memory/archivist/archive-compaction-report-2026-11-20.md (1904B) | 36.2% reduction vs >=30% target = MET, before/after byte sizes logged |
| scribe #9 Institutional Memory Search | memory/scribe/memory-search-goal9-complete-2026-11-20.md (1795B) | backend+UI complete, AC checked; memory_search.py compiles |
| scribe #6 Synthesis Quality Scoring | memory/scribe/goal6-synthesis-quality-verified-2026-11-20.md (1082B) | /api/synthesis/quality 67 scored, vague=35.0(<40) + specific=85.0(>80); quality_score.py compiles |
| orchestrator #9 Cycle Cost Tracker | memory/orchestrator/goal9-cycle-cost-tracker-2026-11-20.md (1201B) | cost_tracker.py compiles, /api/fleet/cost payload verified via direct call, UI chart in ui/core.js |

## Result (after)
`python memory/ops/verify_claims.py --quiet` → **75 REAL / 0 PHANTOM / 5 UNCITED**. Net: +5 REAL, -5 UNCITED, 0 PHANTOM throughout. No downgrade anywhere.

## Remaining 5 UNCITED (for a future pass — all have real artifacts too)
- orchestrator #1 Live Hotload Execution
- orchestrator #2 Fleet Capacity Dashboard v2 → memory/orchestrator/fleet_capacity_2026-11-17.json exists
- orchestrator #10 Fleet Roster Versioning → needs a CONCRETE cycle-N snapshot pointer (real cycle-6/7 snapshots exist; goal text cites only the `cycle-N` template)
- builder #6 State Management Refactor → memory/builder/state_refactor_increment1-2026-11-20.md exists but 'increment1' = partial, needs owner confirmation before close
