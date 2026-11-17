# Goal #8: Error & Empty State Design System — Evidence
Date: 2026-11-18 (auto-loop pass)

## Implementation
Added generic state classes to `ui/app.css` (line ~136, after fleet-specific states):
- `.state-loading` — flex column, centered, uses `var(--sp-24)` padding
- `.spinner` — 20px border spinner, `var(--acc)` top-color, 0.6s linear infinite
- `.state-error` — inherits base layout, color: `var(--err)`
- `.state-empty` — icon at 40% opacity
- `.state-conn-lost` — red dot + retry text
- `@keyframes spin` — rotation animation
- `prefers-reduced-motion` disables spinner animation

All colors/sizes use the token layer (no hard-coded hex/px).

## Usage in panels (≥2 required)
| State | Fleet panel | Goals panel |
|-------|------------|-------------|
| Loading | `.fleet-spinner` (existing) | `.state-loading` + `.spinner` (new, uploads.js goalsLoad) |
| Error | `.fleet-error` + retry-btn (existing) | `.state-error` + icon (new, uploads.js goalsLoad catch) |
| Empty | `.fleet-empty` + SVG (existing) | `.state-empty` + icon (new, uploads.js goalsLoad empty case) |
| Conn lost | `.state-conn-lost` + 5s auto-retry (new, core.js fleetUpdate catch) | — |

## Documentation
Already documented in `memory/portal/components.md` lines 126–133 (pattern table).
No update needed — the doc was ahead of the implementation.

## Acceptance test
- [x] 4 states defined with tokens ✓
- [x] Used in ≥2 panels (fleet + goals) ✓
- [x] Documented in components.md ✓
- [x] Balanced braces verified ✓
