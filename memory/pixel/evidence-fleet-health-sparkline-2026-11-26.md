# Pixel Goal #5 Evidence — Per-host 24h health sparkline (2026-11-26)

## What was built
Added a compact per-host 24h health trend sparkline to `ui/fleet_health.js`:
- Each host badge now shows a 56×16px SVG polyline of its score history over the past 24h.
- Scores accumulate in `localStorage` (key `fh_history_v1`) on each 10s poll; pruned to 24h window.
- Empty state: "—" with aria-label "No trend data yet" when < 2 samples exist.
- Reduced-motion-safe: static SVG polyline, no CSS animation/transition; explicit `prefers-reduced-motion` override in app.css.
- @375px: sparkline scales to 40×14px via media query, no horizontal clipping.

## Files changed
- `ui/fleet_health.js`: +sparkSVG(), +sparkHTML(), +pushHistory(), +pruneHistory(); badge render calls sparkHTML(name); tick() calls pushHistory(sc2) before render.
- `ui/app.css`: +.fh-spark-wrap, +.fh-spark, +.fh-spark-empty, @375px scaling, @prefers-reduced-motion override.

## Verification (structural 11/11)
| Check | Result |
|-------|--------|
| sparkSVG function present | ✓ |
| sparkHTML empty state (< 2 pts → "—") | ✓ |
| pushHistory writes to localStorage | ✓ |
| pruneHistory uses 86400000ms (24h) cutoff | ✓ |
| Per-host badge includes sparkHTML(name) call | ✓ |
| tick() calls pushHistory before render | ✓ |
| Reduced-motion safe (no animation/rAF in JS) | ✓ |
| CSS: .fh-spark-wrap flex container | ✓ |
| CSS: @375px scales to 40×14px | ✓ |
| CSS: prefers-reduced-motion kills transitions | ✓ |
| a11y: role="img" + aria-label with score | ✓ |

SVG coordinate math verified: 5-point sample [80,75,90,60,85] produces correct x/y mapping; flat-line case (all same score) renders without division-by-zero.

## Status: REACHED
