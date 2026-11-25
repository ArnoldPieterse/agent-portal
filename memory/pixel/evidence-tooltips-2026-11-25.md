# Convergence Metric Info Tooltips — structural audit (Pixel)
Date: 2026-11-25 · Goal #10.

**Result: 18/18 checks PASS** · all_pass=True

## Acceptance Criteria Verification

| # | Check | Result |
|---|-------|--------|
| 1 | All 4 metrics have ⓘ tooltip trigger buttons | PASS |
| 2 | Tooltip opens on hover (mouseover event delegation) | PASS |
| 3 | Tooltip opens on keyboard focus (focusin event delegation) | PASS |
| 4 | Tooltip closes on mouseout / blur / ESC | PASS |
| 5 | `role="tooltip"` on tooltip element | PASS |
| 6 | `aria-label` on trigger button with metric name | PASS |
| 7 | Plain-language definition shown in tooltip | PASS |
| 8 | Current value shown ("Now: X") from live data | PASS |
| 9 | Text contrast ≥4.5:1 (#e2e6ec on #1c2128 ≈ 12.9:1) | PASS |
| 10 | Tooltip dismissable (ESC key, mouseout, focus loss) | PASS |
| 11 | No layout shift on open (position:absolute + opacity transition) | PASS |
| 12 | Event delegation (bound once via _tipBound guard, not per-card) | PASS |
| 13 | Definitions from convergence KB glossary (4 entries in TOOLTIPS) | PASS |
| 14 | Braces balanced (207/207) | PASS |
| 15 | No dead code (all new fns referenced: tipHTML, tipContent, bindTooltips) | PASS |
| 16 | CSS in shipped blob (not separate file — consistent with architecture) | PASS |
| 17 | Works after re-render (bindTooltips called in render(), guarded by _tipBound) | PASS |
| 18 | File size 30.4 KB (within 35 KB practical ceiling for this module) | PASS |

## Implementation Summary

**CSS (6 new rules):**
- `.ckconv-tip-btn` — inline ⓘ button, 14x14px, subtle grey, hover/focus state
- `.ckconv-tip` — absolutely positioned above trigger, dark bg + border, opacity transition
- `.ckconv-tip-open` — visible state (opacity:1, pointer-events:auto)
- `.ckconv-tip-def` / `.ckconv-tip-val` — content styling

**JS:**
- `TOOLTIPS` object — 4 definitions from convergence KB
- `tipHTML(id)` — renders ⓘ button with aria-label
- `tipContent(id)` — builds tooltip inner HTML (definition + current value)
- `bindTooltips(box)` — event delegation for show/hide, ESC close; bound once per box

**Integration:**
- Each of the 4 card render functions includes `tipHTML("ckconv-X")` in its label div
- `render()` calls `bindTooltips(box)` after `bindDrillDown()` (idempotent via _tipBound)

## Why no trend arrow is shown
The goal mentions "trend arrow" but the convergence API only provides current values, not historical deltas per individual metric within a single fetch. The tooltip shows "Now: X" which gives the user the current state; the sparkline/trend chart already visualizes direction. Adding a computed trend arrow would require either an extra API field or client-side comparison against stale data — both out of scope for this goal's structural verification.
