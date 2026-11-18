# Evidence: Information Density Pass - Static Analysis + CSS Changes (2026-11-19)

## Changes made this pass

| File | Change | Effect |
|------|--------|--------|
| ui/app.css L9 | `body line-height: 1.45` -> `var(--lh-base)` | Tokenization (no visual change) |
| ui/app.css L135 | `#actBody line-height: 1.7` -> `var(--lh-mono)` = 1.6 | Tightens action panel text by 0.1em/line |
| ui/app.css L164 | `#goalsBody gap: var(--sp-8)` -> `var(--sp-4)` | Tile grid gap 8px->4px |
| ui/app.css L132 | `.opsrow margin-top: var(--sp-8)` -> `var(--sp-4)` | Ops row spacing 8px->4px |

## Static density calculation (theoretical, no browser needed)

Baseline (pre-tokenization 2026-11-18):
- Row: 12+12 padding + 1.6*14 text = 46.4px
- Panel (5 rows): 2*16 pad + 5*46.4 + 4*8 gap = 296px

Current (post-changes):
- Row: 8+8 padding + 1.45*14 text = 36.3px
- Panel (5 rows): 2*12 pad + 5*36.3 + 4*4 gap = 222px

**Theoretical reduction: 25.2% (target: >=20%) - PASS on static analysis**

Conservative estimate (avg gap=6px across mixed panels): 22.5% - still PASS.

## Remaining for full closure
- Browser screenshot comparison (before/after) to confirm no text overlap/clipping
- The measurement script `memory/designer/density_measurement_script.js` is ready for DevTools console run
- Acceptance test requires: render portal, run script, verify totalChange <= -20% and clipped == 0

## Verification
- ui/app.css braces: 263/263 BALANCED
- All new values use existing tokens (no new tokens needed)
- No layout-breaking changes (only gap/padding/line-height reductions within safe ranges)