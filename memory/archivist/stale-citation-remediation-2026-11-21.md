# Stale-Citation Remediation Priorities (from citation-map.json)

Source: memory/archivist/citation-map.json (generated 2026-11-20T13:44:00Z).
Stale = cited file's mtime is NEWER than the citing file's -> the pointer may reference superseded content.
This leaf turns the raw 348-entry list into an actionable, prioritized queue. Companion to Goal 9 (Citation Tracking).

## Triage summary

| Bucket | Count | Action |
|---|---|---|
| Total stale edges | 348 | — |
| INDEX/JSON cited (structural noise) | 104 | No action - these are pointer-map files that legitimately churn; re-run xref_check.py instead of hand-fixing. |
| Genuine, citing file ARCHIVED (frozen snapshot) | 60 | LOW priority - historical goal snapshots are intentionally frozen; do NOT re-point them (breaks provenance). Leave as-is. |
| Genuine, citing file LIVE (actionable) | 184 | **WORK QUEUE** - the only bucket worth fixing. See below. |

## Work queue: live files whose citations may be stale

149 distinct live files carry at least one stale genuine citation.
Top 20 by count (re-check each pointer against the cited file's current content):

| # stale | citing file |
|---|---|
| 5 | `memory/archivist/orphan-remediation-cycle5.md` |
| 4 | `memory/archivist/hostdoc-consistency-v2-2026-11-18.md` |
| 3 | `memory/goals/researcher-log-2026-11-13.md` |
| 3 | `memory/researcher/dcabots-reprompt-atlasq8-gate-r49.md` |
| 2 | `memory/goals.md` |
| 2 | `memory/archivist/hosts-pin-reconciliation-2026-11-14.md` |
| 2 | `memory/archivist/index-integrity-2026-11-15.md` |
| 2 | `memory/archivist/orphan-folder-audit-r42.md` |
| 2 | `memory/archivist/orphan-remediation-fullscan-report.md` |
| 2 | `memory/builder/crossassist-handoff-2026-11-16.md` |
| 2 | `memory/designer/planning-meeting-2026-11-14.md` |
| 2 | `memory/goals/all-goals-2026-11-13.md` |
| 2 | `memory/goals/builder-forecast-archivist-phantom-closure-2026-11-19.md` |
| 2 | `memory/mechanic/auto-loop-pass-2026-11-20c.md` |
| 2 | `memory/mechanic/goal1-discrepancy-reconciled-2026-11-20.md` |
| 2 | `memory/ops/citation-phantom-triage-runbook.md` |
| 2 | `memory/ops/left-orchestrator.md` |
| 2 | `memory/ops/sandbox-egress-triage.md` |
| 2 | `memory/orchestrator/bg-goals-contribution-2026-11-18.md` |
| 2 | `memory/orchestrator/retro_draft_cycle3_2026-11-17.md` |

## Recommended process (per live file)

1. Open the citing file; for each flagged pointer, read the cited leaf's current first heading + date stamp.
2. If content still matches -> no change (false positive from mtime churn).
3. If superseded -> update the pointer to the new leaf, or add a `superseded-by:` line if the old leaf is retained.
4. If the cited leaf was archived -> repoint to memory/archive/... path (keeps citation resolvable).

## Notes / gaps

- mtime-based staleness is a heuristic: a file can be touched without content change (mirror re-write), inflating counts. Treat as a *re-check* queue, not a confirmed-broken list.
- 60 archived-citing entries are deliberately NOT in the work queue (frozen snapshots).
- No false-positive rate measured yet; first pass should sample ~10 live entries to calibrate before bulk action.

Owner: Archivist. Status: prioritization complete; per-file re-check not yet executed.