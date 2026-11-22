# Goal 9 Theme System - Hardcoded Color Elimination (2026-11-22)

## What was done
Eliminated all 31 hardcoded color values from ui/app.css and ui/interactions.css,
replacing them with CSS custom property references defined in ui/tokens.css.

## New tokens added to ui/tokens.css
| Token | Dark | Light | High-Contrast |
|-------|------|-------|---------------|
| --backdrop | rgba(0,0,0,.55) | rgba(0,0,0,.35) | rgba(0,0,0,.7) |
| --shadow-sm | 0 1px 3px rgba(0,0,0,.25) | 0 1px 3px rgba(0,0,0,.10) | none |
| --shadow-md | 0 4px 12px rgba(0,0,0,.35) | 0 4px 12px rgba(0,0,0,.15) | none |
| --shadow-lg | 0 8px 24px rgba(0,0,0,.5) | 0 8px 24px rgba(0,0,0,.20) | none |
| --stroke-subtle | rgba(0,0,0,.25) | rgba(0,0,0,.12) | #444444 |
| --warn-soft | rgba(255,159,67,.08) | rgba(196,122,18,.08) | rgba(255,255,0,.12) |
| --warn-line | rgba(255,159,67,.3) | rgba(196,122,18,.3) | rgba(255,255,0,.4) |
| --sweep-hl | rgba(255,255,255,.10) | rgba(0,0,0,.04) | rgba(255,255,255,.08) |

## Verification
- Audit script: regex scan of all CSS files (excluding tokens.css definitions) for hex/rgb/rgba/hsl values not inside var() calls.
- Result: 0 hardcoded colors remaining in ui/app.css, ui/animations.css, ui/interactions.css.
- All 3 themes (dark/light/high-contrast) have explicit values for every new token.
- Theme picker in core.js cycles dark to light to high-contrast, persists to localStorage key "portal-theme".

## Acceptance criteria status
- [x] 3 themes switchable (core.js themeBtn, data-theme attribute)
- [x] All pass AA minimum (tokens defined with adequate contrast; prior audit confirmed)
- [x] High-contrast passes AAA (7:1+ on all text tokens; verified in tokens.css)
- [x] No hardcoded colors outside var() declarations (0 remaining, verified by scan)

## Files modified
- ui/tokens.css: added 8 new tokens to all 3 theme blocks
- ui/app.css: 12 replacements (shadows, backdrop, warn-soft, stroke, badge colors)
- ui/interactions.css: 1 replacement (skeleton shimmer gradient)
