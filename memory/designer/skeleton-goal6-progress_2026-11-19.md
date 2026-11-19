# Skeleton screens progress (Designer goal #6) - 2026-11-19

Parent: memory/designer/INDEX.md. Status: PROGRESS (not closed - browser render acceptance pending).

## What was built this pass
- `ui/app.css`: appended `.skel` shimmer block after the tour CSS.
  - `@keyframes skel-shimmer` (opacity .35<->.7, 1.5s ease-in-out infinite)
  - `@media(prefers-reduced-motion:reduce){.skel{animation:none;opacity:.45}}`
  - `.skel-row`/`.skel-dot` = fleet row placeholder (flex row + 10px round dot + text lines)
  - `.skel-tile`/`.skel-ring` = goal tile placeholder, geometry mirrors `.gtile` (min-width:170px, 44x44 ring, same padding/border/radius) so real content swap causes NO layout shift
- `ui/core.js` `fleetUpdate()`: before `await api("/api/fleet")`, sets `#fleetBody.innerHTML` to 3 `.skel-row` blocks.
- `ui/uploads.js` `goalsLoad()`: before `await fetch("/api/goals")`, sets `#goalsBody.innerHTML` to 8 `.skel-tile` blocks.

## Why layout-matched (goal acceptance: "no layout shift when real content loads")
Each skeleton reuses the real panel's box model (same min-width, padding, border, radius, ring size). The fetch resolves and overwrites innerHTML with identically-shaped real nodes -> no CLS.

## Verification (in-sandbox, structural)
- core.js braces 215/215, parens 760/760 balanced
- uploads.js braces 251/251, parens 960/960 balanced
- app.css braces 291/291 balanced; all of .skel/.skel-row/.skel-dot/.skel-tile/.skel-ring/@keyframes skel-shimmer/prefers-reduced-motion present
- tokens used by the new block: --line, --panel2, --sp-8, --sp-12 (all defined in ui/tokens.css; 0 undefined)

## Remaining for closure
1. Live-browser render during a simulated ~2s API delay -> capture skeleton state + confirm no CLS on swap. This is the recorded NEEDS-HUMAN browser blocker (memory/ops/blockers.md); hand to Verifier / White-capable seat with Chrome+CDP.
2. Wire remaining 2 panels: timeline strip (`#goalsTimeline`, uploads.js ~L380-422) and uploads file list (`#filesList`/`#filesPanel`).

## Files touched (relative)
- ui/app.css
- ui/core.js
- ui/uploads.js
