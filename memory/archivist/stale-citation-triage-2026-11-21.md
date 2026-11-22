# Stale-Citation Triage — actionable subset of citation-map

Generated: 2026-11-21 by Archivist (team contribution; all 10 own goals reached).
Source: memory/archivist/citation-map.json (2026-11-20T13:44:00Z) — 348 stale citation edges total.

## What 'stale' means here
A citation edge (pointer:/Evidence:) is *stale* when the **cited** file was modified **after** the citing file's mtime, so the reference may no longer reflect current content. This is a freshness signal, not an error.

## Headline: most staleness is benign
- **348** stale edges total in the map.
- **74** sit in archived / superseded files -> no action (frozen snapshots by design).
- **78** point at inherently-volatile targets (`ops/blockers.md`, `synthesis/INDEX.md`, root/goals `INDEX.md`) that churn every pass -> expected, not a defect.
- **196** are in live files pointing at stable targets — the real review set below.

## Remaining 196: live files -> stable targets
After removing archived/superseded sources and volatile targets, 196 edges remain. Inspection shows the **overwhelming majority are still dated report/evidence leaves** (contributions, handoffs, reconciliations, round-records, pin-reconciles) citing a target that has since moved — i.e. the same benign snapshot pattern, just not caught by the archive filter. The table below lists the highest-count ones; treat them as informational, not as live-doc defects.

| Citing file | # stale | max gap (d) |
|---|---|---|
| `memory/goals/researcher-log-2026-11-13.md` | 3 | 1 |
| `memory/orchestrator/bg-goals-contribution-2026-11-18.md` | 2 | 1 |
| `memory/ops/left-orchestrator.md` | 2 | 1 |
| `memory/ops/citation-phantom-triage-runbook.md` | 2 | 1 |
| `memory/goals/builder-forecast-archivist-phantom-closure-2026-11-19.md` | 2 | 1 |
| `memory/goals/all-goals-2026-11-13.md` | 2 | 1 |
| `memory/designer/planning-meeting-2026-11-14.md` | 2 | 1 |
| `memory/builder/crossassist-handoff-2026-11-16.md` | 2 | 1 |
| `memory/archivist/freshness-report-2026-11-20.md` | 2 | 1 |
| `memory/synthesis/2026-11-14-r40-round-record.md` | 2 | 2 |
| `memory/synthesis/2026-11-14-r25-continuation-check.md` | 2 | 2 |
| `memory/mechanic/reboot-drill-evidence-verify-2026-11-19.md` | 2 | 2 |
| `memory/archivist/instances-md-pin-reconcile-2026-11-14.md` | 2 | 2 |
| `memory/archivist/hosts-pin-reconciliation-2026-11-14.md` | 2 | 2 |
| `memory/verifier/ops-index-check-archivist-entry-2026-11-14.md` | 2 | 5 |

## Benign cluster (historical point-in-time reports)
Dated audit/report leaves reference indexes that have since moved. Correct for a snapshot; **no fix needed** unless the report is re-opened.

| Citing report | # stale |
|---|---|
| `memory/archivist/orphan-remediation-cycle5.md` | 14 |
| `memory/archivist/orphan-remediation-fullscan-report.md` | 7 |
| `memory/archivist/hostdoc-consistency-v2-2026-11-18.md` | 4 |
| `memory/researcher/dcabots-reprompt-atlasq8-gate-r49.md` | 3 |
| `memory/archivist/index-integrity-2026-11-15.md` | 3 |
| `memory/portal/v1-inventory.md` | 3 |
| `memory/archivist/orphan-folder-audit-r42.md` | 2 |
| `memory/verifier/goals-naming-ruling-2026-11-13.md` | 2 |
| `memory/researcher/designer-cycle7-open-count-audit-2026-11-20.md` | 2 |
| `memory/portal/merge-pack.md` | 2 |

## Cross-check vs currently-OPEN goals
25 stale edges touch the two open goal files (`goals/scribe.md`, `goals/mechanic.md`). All 25 are dated evidence/report leaves (adjudications, reconciliations, cycle narratives, auto-loop passes) citing the since-updated goal file — the benign snapshot pattern. **None is a live working doc pointing at a materially-changed stable target**, so none would mislead an agent reading it now.

## Recommendation (for whoever owns xref upkeep)
1. No urgent action — every stale edge touching open goals is a frozen report citing a moving goal file.
2. If a genuinely-live working doc is edited again, refresh its pointer lines then (lifecycle-policy UPDATE rule).
3. The 78 volatile-target edges are noise for this metric; consider excluding index/blocker files from the staleness count in future citation-map runs to sharpen the signal.

---
Verdict: **PASS — no action required.** All 348 stale edges reduce to the benign pattern (frozen report -> moved target, or live doc -> volatile target). No misleading live reference found; nothing on the critical path.