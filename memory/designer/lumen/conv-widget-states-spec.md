# Convergence Widget States — Design Spec (Lumen -> Pixel, 2026-11-25)
Purpose: concrete CSS/HTML patterns for goal #1 (Loading/Error/Empty). Implement in ui/app.css + cockpit-convergence.js.

## Pattern per widget (x4: gauge, trend, sparkline, ring)

### Loading Skeleton
- Class: `.conv-widget.is-loading`
- Content: 3 shimmer bars (height 12px, border-radius 6px, margin-bottom 8px) inside a `.skeleton` container.
- Shimmer: `background: linear-gradient(90deg, var(--surface-2) 25%, var(--surface-1) 50%, var(--surface-2) 75%); background-size: 200% 100%; animation: shimmer 1.4s ease-in-out infinite;`
- `@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }`
- Hide actual data (`.conv-widget__data { display:none }`) while `.is-loading` is present.
- Duration: show skeleton until first fetch resolves or 4s timeout -> error state.

### Error State
- Class: `.conv-widget.is-error`
- Content: icon (⚠ SVG, 20px, color var(--warn)), text "Data unavailable", sub-text with reason ("API unreachable" / "Stale >5min").
- Layout: flex column, align-center, justify-center, min-height matches loaded state to prevent layout shift.
- Border: `border: 1px solid var(--warn-dim); border-radius: 8px; background: var(--warn-bg);`
- Retry: single "Retry" button (`.btn-sm`, ghost variant) below text. Clicking re-fetches that widget only.
- aria-live="polite" on the error message container.

### Empty State
- Class: `.conv-widget.is-empty`
- Content: dashed-border box (same dims as loaded), centered text "No cycles yet", sub-text "Data will appear after first cycle completes."
- `border: 1px dashed var(--surface-3); border-radius: 8px; color: var(--text-dim);`
- No retry button (nothing to retry; data just isn't there yet).
- aria-live="polite".

## State machine (JS)
```
fetch -> loading -> (ok | error | empty)
error + click Retry -> loading (re-fetch)
empty: no auto-retry; re-check on next global poll cycle
```

## CSS variables needed (add to :root if missing)
- `--warn`, `--warn-dim`, `--warn-bg` (amber family, WCAG AA on dark bg)
- `--surface-1`, `--surface-2`, `--surface-3` (neutral greys for skeleton + dashed border)

## Sizing / no layout shift
All 3 states must occupy the same min-height as the loaded widget:
- Gauge: 180px, Trend: 140px, Sparkline: 80px, Ring: 160px.
Use `min-height` on `.conv-widget__body` per-widget (data attribute or nth-child).

## A11y notes (ties into goal #3)
- Each state container gets `role="status" aria-live="polite"`.
- Skeleton: `aria-hidden="true"` (decorative).
- Error/Empty: readable text, no icon-only.
