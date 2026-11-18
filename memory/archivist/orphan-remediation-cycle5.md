# Orphan Node Remediation Log - Cycle 5
Generated: 2026-11-19 by Orchestrator (assist for Archivist goal #4)

## Summary
| Metric | Value |
|--------|-------|
| Total nodes in KG | 286 |
| Orphans before remediation | 154 (53.8%) |
| Marked intentionally standalone | 103 |
| Remaining needing links | 51 (17.8%) |
| Target | <5% (14 orphans max) |

## Classification Rules Applied
1. INDEX.md files -> standalone (entry points)
2. .py / .sh / .ps1 scripts -> standalone (tools)
3. .json / .jsonl data -> standalone (consumed by scripts)
4. Dated evidence/report artifacts -> standalone (point-in-time snapshots)
5. Goal files in memory/goals/ -> standalone (ledger-referenced)
6. Archived/superseded content -> standalone (intentionally unlinked)
7. Seat MEMORY.md / TODO.md -> needs-link (should be in parent INDEX)
8. Other content -> needs-link

## Nodes Marked Standalone (103)
- `memory/archivist/INDEX.md` — Entry point / navigation hub - no inbound link needed
- `memory/archivist/bundle-v2-item1-staleness-r73-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/archivist/dream-big-wishes-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/archivist/ground-truth-pale-r64-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/archivist/run1_baseline.json` — Data file - consumed by scripts, not linked from prose
- `memory/archivist/supersession_check.py` — Tool script - invoked directly, not referenced by content
- `memory/builder/INDEX.md` — Entry point / navigation hub - no inbound link needed
- `memory/builder/arnold-restart-r19.ps1` — Script file - invoked directly
- `memory/builder/builder-exec-sweep-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/builder/index-repin-r65-v21-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/builder/index-v22-surgical-fixes-confirmed-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/builder/synthesis-index-apply-handoff-r62-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/builder/truncation-e2e-verify-2026-11-16.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/INDEX.md` — Entry point / navigation hub - no inbound link needed
- `memory/designer/a6b-candidate-diff-r47-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/conflict-resolution-merged-canonical-2026-11-15.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/goals-1-2-3-6-10-evidence-2026-11-16.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/goals-patch-apply-2026-11-15.py` — Tool script - invoked directly, not referenced by content
- `memory/designer/index-v22-promotion-r71-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/live-root-not-v2-r62-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/ops-panel-hierarchy-evidence-2026-11-15b.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/planning-meeting-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/px-scale-spec-2026-11-15.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/stamp-verify-r61-107cbd93-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/token-gap-analysis-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/token-refactor-2026-11-15.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/token_audit.py` — Tool script - invoked directly, not referenced by content
- `memory/designer/v21-merge-c820e755-r64-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/designer/wcag_contrast_live.py` — Tool script - invoked directly, not referenced by content
- `memory/goals/2026-11-13-agent-goals.md` — Goal file - referenced by ledger, not content-linked
- `memory/goals/INDEX.md` — Entry point / navigation hub - no inbound link needed
- `memory/goals/archive/2026-11-13-agent-goals-SUPERSEDED-partial.md` — Goal file - referenced by ledger, not content-linked
- `memory/goals/archive/README.md` — Goal file - referenced by ledger, not content-linked
- `memory/goals/archive/archivist-2026-11-16.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/goals/archive/cycle2-2026-11-17/2026-11-13-agent-goals.md` — Goal file - referenced by ledger, not content-linked
- `memory/goals/archive/cycle2-2026-11-17/archivist.md` — Goal file - referenced by ledger, not content-linked
- `memory/goals/archive/cycle2-2026-11-17/cycle2-proposals-raw-2026-11-16.txt` — Dated evidence/report artifact - point-in-time snapshot
- `memory/goals/archive/cycle2-2026-11-17/designer.md` — Goal file - referenced by ledger, not content-linked
- `memory/goals/archive/cycle2-2026-11-17/forecast-mechanic1-adaptive-probe-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/goals/archive/cycle2-2026-11-17/mechanic-goal4-forecast-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/goals/archive/cycle2-2026-11-17/researcher.md` — Goal file - referenced by ledger, not content-linked
- `memory/goals/archive/designer-2026-11-16.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/goals/archive/orchestrator-2026-11-13.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/goals/cycle2-proposals-raw-2026-11-16.txt` — Dated evidence/report artifact - point-in-time snapshot
- `memory/goals/forecast-mechanic1-adaptive-probe-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/goals/mechanic-goal4-forecast-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/mechanic/INDEX.md` — Entry point / navigation hub - no inbound link needed
- `memory/mechanic/ac_a2_live_leg_r21.py` — Tool script - invoked directly, not referenced by content
- `memory/mechanic/adaptive-probe-poller-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/mechanic/goal-ledger-current.json` — Data file - consumed by scripts, not linked from prose
- `memory/mechanic/goal2_mirror_heal_productionized-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/mechanic/memory_mirror_r16.py` — Tool script - invoked directly, not referenced by content
- `memory/ops/memory-trim-archive-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/ops/researcher-seat-verify-r7-2026-11-13.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/ops/verifier-healthcheck-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/ops/verifier-pin-crosscheck-2026-11-15.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/orchestrator/INDEX.md` — Entry point / navigation hub - no inbound link needed
- `memory/portal/mirror-clobber-pattern-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/portal/planning-2026-11-13.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/projects/INDEX.md` — Entry point / navigation hub - no inbound link needed
- `memory/researcher/INDEX.md` — Entry point / navigation hub - no inbound link needed
- `memory/researcher/load-probe-current-diskstate-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/researcher/outside-click-false-alarm-r76-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/researcher/pin-consistency-check-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/researcher/probe-canonical-pin-correction-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/researcher/r20-lane-status-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/researcher/r27-probe-n-semantics-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/researcher/r27b-live-leg-pass-condition-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/researcher/r61-reconcile-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/researcher/stamp-adjudication-crosscheck-r54-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/researcher/stamp-target-correction-r75-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/researcher/sync-clobber-analysis-2026-11-13.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/researcher/synthesis-index-canonical-r73-24of24-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/researcher/wcag-aa-and-tokenization-reverify-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/scribe/INDEX.md` — Entry point / navigation hub - no inbound link needed
- `memory/scribe/cycle-narrative-thread-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/scribe/supersession-audit-2026-11-17.json` — Data file - consumed by scripts, not linked from prose
- `memory/scribe/supersession-report-2026-11-16.json` — Data file - consumed by scripts, not linked from prose
- `memory/scribe/supersession_check.py` — Tool script - invoked directly, not referenced by content
- `memory/scribe/synthesis-index-canonical-r61-0517db38-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/scribe/synthesis-index-canonical-r72-485a6558-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/scribe/synthesis-index-canonical-r73-8e194239-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/scribe/synthesis-index-eef00527-superseded-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/synthesis/planning-meeting-minutes-v2-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/INDEX.md` — Entry point / navigation hub - no inbound link needed
- `memory/verifier/a4a5-candidate-persisted-r40-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/a4a5-lineage-repro-r39-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/a4a5-verify-r38-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/ac-a2-r29-probe-restage-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/ac-a2-r71b-sweep-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/ac-a2-r73-final-reconciliation-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/ac-a2-r76-final-sweep-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/ac-a2-r81-autocontinue-final-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/ac-a2-r82-record-correction-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/black-seat-sweep-r75b-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/lww-clobber-evidence-2026-11-13.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/planning-meeting-gate-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/r30-probe-drift-adjudication-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/r44-closeout-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/r45-closeout-2026-11-14.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/theme-css-block-absent-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/verifier/ui-slices-verify-2026-11-17.md` — Dated evidence/report artifact - point-in-time snapshot
- `memory/workspace/INDEX.md` — Entry point / navigation hub - no inbound link needed

## Nodes Requiring Links (51)
- `memory/archivist/index-pointer-batch-r42.md` — Content file with no inbound edges; suggest adding pointer from memory/archivist\INDEX.md
- `memory/builder/MEMORY.md` — Should be linked from memory/builder/INDEX.md
- `memory/builder/TODO.md` — Should be linked from memory/builder/INDEX.md
- `memory/builder/anomaly-ar14-writepath-evidence.md` — Content file with no inbound edges; suggest adding pointer from memory/builder\INDEX.md
- `memory/builder/index-repin-r25-rollback.md` — Content file with no inbound edges; suggest adding pointer from memory/builder\INDEX.md
- `memory/builder/white-rename-consistency-r20.md` — Content file with no inbound edges; suggest adding pointer from memory/builder\INDEX.md
- `memory/builder/white-rename-consistency-r21-addendum.md` — Content file with no inbound edges; suggest adding pointer from memory/builder\INDEX.md
- `memory/designer/a4-dual-base-verify-r27.md` — Content file with no inbound edges; suggest adding pointer from memory/designer\INDEX.md
- `memory/designer/files-panel-hunks-r5.md` — Content file with no inbound edges; suggest adding pointer from memory/designer\INDEX.md
- `memory/designer/panel-discipline-r20.md` — Content file with no inbound edges; suggest adding pointer from memory/designer\INDEX.md
- `memory/mechanic/__pycache__/ac_a2_live_leg_r21.cpython-313.pyc` — Content file with no inbound edges; suggest adding pointer from memory/mechanic/__pycache__\INDEX.md
- `memory/mechanic/__pycache__/memory_mirror_r16.cpython-313.pyc` — Content file with no inbound edges; suggest adding pointer from memory/mechanic/__pycache__\INDEX.md
- `memory/ops/merge-queue/TODO_completed.md.73b7b5b6d3` — Content file with no inbound edges; suggest adding pointer from memory/ops/merge-queue\INDEX.md
- `memory/ops/merge-queue/memory_mirror.py.0e026c89c0` — Content file with no inbound edges; suggest adding pointer from memory/ops/merge-queue\INDEX.md
- `memory/ops/merge-queue/memory_mirror.py.39114dbdfa` — Content file with no inbound edges; suggest adding pointer from memory/ops/merge-queue\INDEX.md
- `memory/ops/merge-queue/memory_mirror.py.56e34017e3` — Content file with no inbound edges; suggest adding pointer from memory/ops/merge-queue\INDEX.md
- `memory/ops/merge-queue/memory_mirror.py.75be858c9c` — Content file with no inbound edges; suggest adding pointer from memory/ops/merge-queue\INDEX.md
- `memory/ops/merge-queue/memory_mirror.py.77db23e68d` — Content file with no inbound edges; suggest adding pointer from memory/ops/merge-queue\INDEX.md
- `memory/ops/merge-queue/memory_mirror.py.d10e23eab7` — Content file with no inbound edges; suggest adding pointer from memory/ops/merge-queue\INDEX.md
- `memory/ops/merge-queue/memory_mirror.py.f5216f8a2a` — Content file with no inbound edges; suggest adding pointer from memory/ops/merge-queue\INDEX.md
- `memory/ops/pin-guard-extension-ui-files.md` — Content file with no inbound edges; suggest adding pointer from memory/ops\INDEX.md
- `memory/orchestrator/white-apply-bundle-v2-r45.md` — Content file with no inbound edges; suggest adding pointer from memory/orchestrator\INDEX.md
- `memory/portal/merge-pack.md` — Content file with no inbound edges; suggest adding pointer from memory/portal\INDEX.md
- `memory/portal/system-map.md` — Content file with no inbound edges; suggest adding pointer from memory/portal\INDEX.md
- `memory/portal/upgrade-plan.md` — Content file with no inbound edges; suggest adding pointer from memory/portal\INDEX.md
- `memory/portal/v1-inventory.md` — Content file with no inbound edges; suggest adding pointer from memory/portal\INDEX.md
- `memory/portal/v1-upgrades-decisions.md` — Content file with no inbound edges; suggest adding pointer from memory/portal\INDEX.md
- `memory/researcher/open-questions-log.md` — Content file with no inbound edges; suggest adding pointer from memory/researcher\INDEX.md
- `memory/researcher/two-pin-index-adjudication-r32.md` — Content file with no inbound edges; suggest adding pointer from memory/researcher\INDEX.md
- `memory/scribe/TODO.md` — Should be linked from memory/scribe/INDEX.md
- `memory/scribe/__pycache__/supersession_check.cpython-313.pyc` — Content file with no inbound edges; suggest adding pointer from memory/scribe/__pycache__\INDEX.md
- `memory/scribe/supersession-pointer-spec.md` — Content file with no inbound edges; suggest adding pointer from memory/scribe\INDEX.md
- `memory/synthesis/2026-11-14-ac-a2-sweep-closeout.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/2026-11-14-dream-big-r58-final.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/2026-11-14-final-closeout-supersession.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/2026-11-15-public-repo-ip-decision.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/2026-11-15-round-continuation.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/2026-11-15-status-report.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/2026-11-16-portal-status-report.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/2026-11-16-r1-round-record-DRAFT.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/2026-11-16-r1-round-record.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/2026-11-16-status-thread-contradictions.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/cycle-narrative.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/index-pointer-batch-r57-consolidated.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/index-pointer-batch-r58-canonical-append.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/index-pointer-handoff-r38.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/index-replay-r81-24of24-canonical.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/synthesis/supersession-policy-baseline.md` — Content file with no inbound edges; suggest adding pointer from memory/synthesis\INDEX.md
- `memory/verifier/MEMORY.md` — Should be linked from memory/verifier/INDEX.md
- `memory/verifier/ac-a2-closure-r19.md` — Content file with no inbound edges; suggest adding pointer from memory/verifier\INDEX.md
- `memory/verifier/ac-a2-final-state-r20.md` — Content file with no inbound edges; suggest adding pointer from memory/verifier\INDEX.md

---
*Orchestrator assist for Archivist goal #4. Next step: create links for 'needs-link' nodes from their parent INDEX.md files.*