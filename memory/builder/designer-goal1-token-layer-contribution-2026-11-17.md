# Builder contribution to Designer Goal #1 (design token layer) - 2026-11-17

## What was done
Added missing token categories to ui/app.css :root block and replaced all hard-coded values:

| Category | Tokens added | Replacements made |
|----------|-------------|-------------------|
| Radius   | --radius-sm(6px), --radius-md(8px), --radius-lg(12px) | 30 instances |
| Shadow   | --shadow-pop(0 8px 24px rgba(0,0,0,.5)) | 1 instance |
| Duration | --dur-fast(.15s), --dur-med(.2s) | 9 instances |

Also added `@media(prefers-reduced-motion:reduce)` block (advances goal #4).

## Verification
- 0 remaining hard-coded border-radius values (non-50%)
- 0 remaining hard-coded box-shadow values  
- All 52 var() references have matching :root definitions
- 7 rgba() overlay tints remain (theme-dependent composites - candidate for next pass)

## Remaining for full closure of goal #1
- Tokenize the 7 rgba() composite colors (need theme-aware approach since they layer over --panel/--bg)
- Designer to verify visual parity in both themes after this change
