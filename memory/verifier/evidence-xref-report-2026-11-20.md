# Evidence Cross-Reference Graph Report
**Generated:** 2026-11-20 22:28

## Summary
- Total references scanned: 39
- Goal files with references: 9
- Dangling (broken) references: 0

## Status: ALL REFERENCES RESOLVED
No broken pointers or evidence references found.

## Edge List (complete)
| Source | Line | Type | Target | Exists |
|--------|------|------|--------|--------|
| memory/goals/archivist.md | 5 | pointer | `memory/archivist/index-sweep-2026-11-13.md` | Y |
| memory/goals/archivist.md | 7 | pointer | `memory/archivist/knowledge_graph.py` | Y |
| memory/goals/builder.md | 5 | pointer | `memory/builder/apply_a4_a5_r35.py` | Y |
| memory/goals/builder.md | 9 | pointer | `memory/builder/error_boundary_increment3-2026-11-20.md` | Y |
| memory/goals/builder.md | 11 | pointer | `memory/builder/component_refactor_regression_2026-11-20.md` | Y |
| memory/goals/builder.md | 15 | pointer | `memory/builder/designer-goal2-fleet-states-2026-11-18.md` | Y |
| memory/goals/builder.md | 17 | pointer | `memory/builder/verify_theme_toggle_2026-11-17.md` | Y |
| memory/goals/designer.md | 5 | pointer | `memory/designer/contrast-audit-live-2026-11-20.md` | Y |
| memory/goals/designer.md | 7 | pointer | `memory/designer/goal2-fleet-states-2026-11-18.md` | Y |
| memory/goals/designer.md | 9 | pointer | `memory/designer/goal1-interaction-system-live-2026-11-20.md` | Y |
| memory/goals/designer.md | 13 | pointer | `memory/designer/goal2-animation-consumers-landed-2026-11-20.md` | Y |
| memory/goals/designer.md | 23 | pointer | `memory/designer/css-bundle-budget-2026-11-17.md` | Y |
| memory/goals/mechanic.md | 13 | pointer | `memory/mechanic/goal6-dep-gen-built-2026-11-17.md` | Y |
| memory/goals/mechanic.md | 15 | pointer | `memory/mechanic/reboot-drill-evidence-verify-2026-11-19.md` | Y |
| memory/goals/mechanic.md | 21 | pointer | `memory/mechanic/capacity-report-2026-11-20.md` | Y |
| memory/goals/mechanic.md | 23 | pointer | `memory/mechanic/runbook-gap-analysis-2026-11-17.md` | Y |
| memory/goals/orchestrator.md | 7 | pointer | `memory/orchestrator/fleet_capacity_2026-11-17.json` | Y |
| memory/goals/orchestrator.md | 9 | pointer | `memory/orchestrator/goal3-auto-transition-ext-2026-11-20.md` | Y |
| memory/goals/orchestrator.md | 11 | pointer | `memory/orchestrator/goal9-perf-radar-backend-done-2026-11-17.md` | Y |
| memory/goals/orchestrator.md | 13 | pointer | `memory/orchestrator/goal5-binding-audit-progress-2026-11-20.md` | Y |
| memory/goals/orchestrator.md | 23 | pointer | `memory/orchestrator/retro_draft_cycle3_2026-11-17.md` | Y |
| memory/goals/researcher.md | 5 | pointer | `memory/researcher/unified-loader-offline-surface-2026-11-20.md` | Y |
| memory/goals/researcher.md | 7 | pointer | `memory/researcher/residency-matrix-offline-surface-2026-11-20.md` | Y |
| memory/goals/researcher.md | 9 | pointer | `memory/researcher/overnight-unload-histogram-2026-11-18.md` | Y |
| memory/goals/researcher.md | 11 | pointer | `memory/researcher/archivist-goal3-freshness-verify-2026-11-20.md` | Y |
| memory/goals/researcher.md | 13 | pointer | `memory/researcher/model-benchmark-2026-11-16.md` | Y |
| memory/goals/researcher.md | 15 | pointer | `memory/researcher/kg_integrity_bug_check.py` | Y |
| memory/goals/researcher.md | 21 | pointer | `memory/researcher/evidence-source-scorer-2026-11-18.md` | Y |
| memory/goals/scheduled-background.md | 13 | pointer | `memory/mechanic/goal6-dep-gen-built-2026-11-17.md` | Y |
| memory/goals/scheduled-background.md | 14 | pointer | `memory/mechanic/test_chaos_drill_sim.py` | Y |
| memory/goals/scheduled-background.md | 15 | pointer | `memory/scribe/goal-setting-round-compression-2026-11-13.md` | Y |
| memory/goals/scheduled-background.md | 16 | pointer | `memory/verifier/smb_drift_detector.py` | Y |
| memory/goals/scribe.md | 7 | pointer | `memory/scribe/memory-search-goal9-complete-2026-11-20.md` | Y |
| memory/goals/scribe.md | 9 | pointer | `memory/scribe/cycle_narrative.py` | Y |
| memory/goals/scribe.md | 15 | pointer | `memory/scribe/chain_check.py` | Y |
| memory/goals/scribe.md | 23 | pointer | `memory/scribe/goal6-synthesis-quality-verified-2026-11-20.md` | Y |
| memory/goals/verifier.md | 15 | pointer | `memory/verifier/MEMORY.md` | Y |
| memory/goals/verifier.md | 19 | pointer | `memory/verifier/MEMORY.md` | Y |
| memory/goals/verifier.md | 21 | pointer | `memory/verifier/MEMORY.md` | Y |

## Method
- Scanned all `memory/goals/*.md` (excluding archive/)
- Patterns: `(pointer: <path>)` and `Evidence: <path>`
- Placeholder refs (relpath, <...>, ...) excluded
- Target existence checked via os.path.exists()