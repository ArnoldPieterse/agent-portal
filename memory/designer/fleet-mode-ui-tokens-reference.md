# Fleet Mode UI — Design Token Reference (Cycle 15)

Purpose: Quick lookup for Builder/Verifier when adding new mode-aware UI elements.
All 6 modules are conflict-free (no overlapping selectors, single z-index layer at 99 for ARIA).

## Mode Color Tokens (from tokens.css)
| Mode | CSS Var | Usage |
|------|---------|-------|
| WORK | `--ok` | green tint for active/healthy state |
| MAINTENANCE | `--warn` | amber tint for in-progress maintenance |
| IDLE | `--dim` | grey/muted for dormant state |

All mode-aware components use `color-mix(in srgb, var(--mode-color) 15%, transparent)` for backgrounds.
Never hardcode hex; always derive from these three vars.

## Spacing Scale (from tokens.css)
- `--sp-4` = 4px (tight inline gaps)
- `--sp-8` = 8px (card padding min)
- `--sp-14` = 14px (segment button padding)
- `--sp-20` = 20px (panel gaps)
- `--sp-24` = 24px (section margins)

## Font Sizes
- `--fs-12` = 12px (labels, timestamps)
- `--fs-14` = 14px (body text, buttons)
- `--fs-16` = 16px (panel titles)
- `--fs-20` = 20px (hero text)

## Module Inventory (ui/ directory)
| File | Purpose | @import position |
|------|---------|-----------------|
| tokens.css | Design tokens (colors, spacing, font) | 1st |
| fleet-mode-aria.css | ARIA live region + focus-visible styles | 2nd |
| fleet-mode-transition.css | 400ms bg-color transition + FLIP helpers | 3rd |
| pass-budget-gauge.css | Circular SVG gauge styling | 4th |
| mode-history-timeline.css | Horizontal timeline segments | 5th |
| maintenance-task-cards.css | 4-col card grid for idle agents | 6th |

JS modules loaded dynamically via core.js (line ~605-632):
cockpit-mode-layout, fleet-mode-transition, pass-budget-gauge, mode-history-timeline,
maintenance-task-cards, fleet-mode-aria, convergence-ring, productivity-sparklines

## Stacking Context
- z-index: 99 → ARIA live region (fixed, top-right) — the ONLY elevated layer
- All other panels use default stacking (z-index: 0 or auto)
- FLIP animations use `transform` not `position` to avoid creating new stacking contexts

## Reduced Motion
All animation-bearing modules include:
```css
@media (prefers-reduced-motion: reduce) {
  * { transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; }
}
```
This is in fleet-mode-transition.css and applies globally.

## Breakpoints
- ≥1440px: full layout (4-col grids, horizontal timelines)
- 768–1439px: compressed (2-col cards, scrollable timeline)
- <768px: single column, icon-only timeline, stacked panels

## ARIA Patterns Used
- `aria-live="polite"` on mode-change announcement region
- `aria-valuenow` / `aria-valuemin` / `aria-valuemax` on gauges and rings
- `role="status"` for non-critical updates (sparkline tooltips)
- All interactive elements have visible focus styles (`:focus-visible` with 2px outline)
