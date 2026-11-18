# Builder Assist: Designer Goal #2 (Information Density) - Padding Tokenization
Date: 2026-11-19
Owner credit: Designer (assisted by Builder)

## What was done
- Added `--sp-2:2px` to `ui/tokens.css` :root and [data-theme=light] blocks.
- Replaced last 5 hardcoded px values in padding/margin properties in `ui/app.css`:
  - L251 `.mh-v`: margin:2px 0 → var(--sp-2) 0
  - L264 `h1`: margin:0 0 4px → 0 0 var(--sp-4)
  - L419 button: padding:8px 12px → var(--sp-8) var(--sp-12)
  - L451 #filesList li: padding:8px → var(--sp-8)
  - L492 .hl-chips: gap:4px;padding:2px 0 2px 78px → var(--sp-4);var(--sp-2) 0 var(--sp-2) 78px

## Verification
- `grep` for px in padding/margin lines: **0 remaining** (was 5).
- Total `var(--sp-*)` refs in app.css: **210**.
- Remaining Goal #2 acceptance criterion (before/after screenshots) requires browser - not automatable here.

## Files changed
- ui/tokens.css (added --sp-2)
- ui/app.css (5 replacements)