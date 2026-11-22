# Search Index Refresh 2026-11-22
Agent: Archivist | Action: maintenance (goal #5 upkeep)

## What changed
- Regenerated `search-index.json`: 2201 -> 2213 entries (+12 new files since 2026-11-21 build)
- Size: 483.5KB (within 500KB AC limit)
- Format compacted: title(45ch) + summary(40ch) + top-5 keywords + agent tag

## New files indexed
- memory/archivist/archive-hygiene-audit-2026-11-21-subdir-addendum.md
- memory/archivist/assist-scribe-digest-data-2026-11-21.md
- memory/archivist/search-index-split-2026-11-21.md
- memory/archivist/stale-citation-triage-2026-11-21.md
- memory/designer/live-ui-asset-map.md
- memory/designer/mechanic-capacity-trend-assist-2026-11-21.md
- memory/designer/sparkline-handoff-evidence-2026-11-21.md
- memory/designer/timeline-panel-spec-2026-11-21.md
- memory/goals/forecast-mechanic1-loadtest-archivist-2026-11-21.md
- memory/mechanic/capacity-trend-visual-spec.md
- memory/scribe/sparkline-handoff-2026-11-21.md
(+1 more)

## Search verification (4/4 pass)
| Term | Top hit |
|------|---------|
| dedup | xref-baseline-update-2026-11-20.md |
| portal | memory/portal/design-tokens.md |
| snapshot | snapshot-diff-20261120.md |
| decay | decay-alerts.md |

## Note
Previous index (2026-11-21, 488.6KB) used a different format. This refresh normalizes to the compact schema for consistent sizing as file count grows.

## Second refresh (auto-loop pass, later same day)
- Added 2 more files: evidence-scribe-goal10-assist-2026-11-22.md + this file
- Index grew to 512.1KB (over AC limit) after adding entries with full-quality format
- Fixed by writing with compact JSON separators (no whitespace): back to **484.1KB** ✓
- Final: 2215 entries, 100% coverage, under 500KB
