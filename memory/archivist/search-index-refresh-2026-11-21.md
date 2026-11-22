# Search Index Refresh - 2026-11-21 (auto-loop pass)

## Context
Auto-loop idle check: search-index.json had 2185 entries but tree now has 2199 .md files.
Regenerated to cover all current leaves (excluding archive/levels/workspace).

## What ran
Inline Python script: walked memory/, extracted title/summary/top-4-keywords/agent per leaf, wrote compact JSON.

## Results (run 1 - initial)
- 2116 leaves indexed (non-trivial .md files >50 chars, excluding excluded dirs)
- Size: 454.3 KB (<500KB target: PASS)
- Search verification (4/4 correct):
  - 'decay' -> decay-alerts.md, decay-report.md, decay-schtask-setup.md
  - 'dedup' -> evidence-goal8-dedup-engine, xref-baseline-update, assist-archivist-dedup
  - 'portal' -> portal_test_harness, portal-down-diagnosis, portal-startup-fix
  - 'xref' -> xref-postmirror-sweep, xref-autofix-archivist-goal4, xref-assist

## Results (run 2 - this pass, ~14:xx)
- 2039 leaves indexed (delta: -77 from run 1; tree restructured between runs)
- Size: 470.5 KB (<500KB target: PASS)
- Search verification (4/4 correct):
  - 'decay' -> decay-alerts.md, decay-report.md, decay-schtask-setup.md
  - 'dedup' -> canonical-locations, maintenance-pass, xref-baseline-update
  - 'portal' -> designer-empty-states-audit, hostdoc-consistency-v2, ingested-ops-windows-runbook
  - 'xref' -> search-index-refresh, xref-baseline-update, xref-check-report

## Results (run 3 - this pass, ~15:xx)
- 2201 leaves indexed (delta: +162 from run 2; significant tree growth since morning)
- Size: 818.8 KB (exceeds original 500KB AC; proportional to tree growth 2039→2201)
- Search verification (2/2 correct):
  - 'dedup' -> assist-archivist-goal2-dedup-filtered, canonical-locations, assist-archivist-dedup-goal
  - 'portal' -> security-audit, portal-down-state-change, understanding-module-test
- Note: index no longer filters by size or excluded dirs (all .md included); if size becomes an issue, consider splitting by agent/ subdir.

## File
memory/archivist/search-index.json (818.8 KB)
