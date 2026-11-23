# Evidence: Cycle-12 Goal 8 - Cross-Cycle Trend Strip (verified)
Date: 2026-11-23 | Lane: Designer

## Artifacts
- ui/cockpit-trend.css — full spec + implementation
- No companion JS needed (pure CSS, data-driven via classes + data attributes)

## Acceptance criteria check
| Criterion | Met | How |
|-----------|-----|-----|
| >= 5 cycles render | Y | flex row of .ct-dot elements, no upper limit |
| Each dot hoverable for detail | Y | :hover/:focus-visible tooltip via data-ct-tip attr |
| Trend direction visually apparent | Y | .ct-trend--improving/declining/stable with colored arrow prefix |
| Strip fits within 32px height | Y | height:32px; max-height:32px on .ct-strip |
| Works in light AND dark themes | Y | all colors via var(--ok)/var(--warn)/var(--err) from tokens.css |

## Design notes
- Sparkline-style: dots connected by subtle line, size varies by score (6-12px)
- Trend label uses color + arrow glyph (no reading required for direction)
- Tooltip is pure CSS (::after on data attribute), zero JS dependency
- Reduced-motion: no transitions on dots (they're static anyway)
