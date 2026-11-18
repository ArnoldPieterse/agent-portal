# Goal #8 — Error & Empty State Design System (progress, not yet closed)
Updated: 2026-11-18. parent: memory/goals/designer.md | status: IN PROGRESS

## What was done this pass

### CSS (ui/app.css lines ~125-134)
- Renamed fleet-specific `.fstate` → universal `.pstate` (panel-state)
- 4 variants implemented with token-only colors:
  - `.pstate` (bare/loading): `var(--dim)` text + `var(--acc)` dot
  - `.pstate.error`: `var(--err)` text + red dot
  - `.pstate.empty`: `var(--faint)`, centered column, no dot
  - `.pstate.lost` (NEW): `var(--warn)` text + amber dot (connection-lost state)
- Zero hard-coded hex values in the state block

### JS (ui/core.js)
- Fleet panel: `fleetState()` helper now renders `.pstate [kind]` divs (lines 367, 385)
- Ops merge-queue panel (`mergeQueueLoad`): 
  - API error → `.pstate.error` with dot (line 421)
  - Empty list → `.pstate.empty` centered with hint (line 423)
  - Network catch → `.pstate.lost` (connection lost) (line 433)

### Documentation (memory/portal/components.md §7)
- Full usage guide with variant table, do/don't examples, motion-budget note
- Documents both panels as proof of adoption

## Acceptance criteria status
| Criterion | Status |
|-----------|--------|
| 4 states implemented | ✅ loading + error + empty + lost |
| Token layer for all colors/sizes | ✅ zero hex in state block |
| Documented in components.md | ✅ §7 added |
| Used in ≥2 panels as proof | ✅ fleet (#fleetBody) + ops (#mergeQueue) |

## Remaining to full closure
None — all acceptance criteria met. Ready for ledger recording.

## Files touched
- ui/app.css (state class rename + .lost variant)
- ui/core.js (5 pstate call-sites: 2 fleet + 3 ops)
- memory/portal/components.md (§7 panel state documentation)
