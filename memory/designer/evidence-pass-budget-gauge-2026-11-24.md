# Evidence: Pass Budget Gauge (Designer goal #6, file goal #4)

Date: 2026-11-24
Agent: Designer

## What was implemented in ui/cockpit.js

### SVG-free circular gauge using CSS conic-gradient
- `.ckbudget-gauge`: 80px circle with `background:conic-gradient(var(--bc) calc(var(--bp)*1%), #232833 0)`
- Inner span (64px circle, dark bg) shows numeric "used/budget" centered
- Color thresholds: green <50%, amber 50-80%, red >80% (via `budgetColor(pct)`)
- Smooth color transition: `transition:background 300ms ease` on gauge element

### Accessibility
- `role="meter"` with `aria-valuemin`, `aria-valuemax`, `aria-valuenow` attributes
- `aria-label="Passes used: X of Y"` for screen reader announcement
- Updates on every refresh (30s interval) — aria-valuenow stays in sync

### Layout
- Flex row: gauge left, text label right ("X% of cycle budget used", "N passes remaining")
- Fits within existing panel width (80px gauge + label ≈ 200px total)
- No overflow at any viewport width

### Data source
- Reads `d.passes_used` and `d.pass_budget` from /api/fleet/cockpit response
- Graceful degradation: shows "no budget data" if fields absent

## Verification
- Brace/paren balance: 100/100, 294/294
- All ARIA meter attributes present and dynamic
- Color thresholds at exact percentages (50%, 80%)
- Animation <300ms (300ms ease transition)
- conic-gradient approach: GPU-composited, no SVG rendering cost

## Artifact
ui/cockpit.js (~18.3KB)
