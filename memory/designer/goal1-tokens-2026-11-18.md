# Goal #1 Evidence: Design Token System
Date: 2026-11-18

## What was done
1. Created `ui/tokens.css` with 60 design tokens:
   - 37 color tokens (base palette + semantic extensions)
   - 6 spacing scale values (--sp-4 through --sp-24)
   - 8 typography scale values (--fs-10 through --fs-24)
   - 5 border-radius tokens (--br-xs through --br-full)
   - Line-height + vertical rhythm tokens

2. Updated `ui/app.css`:
   - Added @import url('tokens.css') at top
   - Removed inline :root block (now lives in tokens.css)
   - Replaced all 36 hard-coded hex colors with var(--token) references
   - Replaced all 41 border-radius px values with var(--br-*) references
   - Replaced all font-size px values with var(--fs-*) references

## Acceptance test result
- grep for hex colors in ui/*.css outside tokens.css: 0 hits [PASS]
- All components use var(--token) [PASS]
- No hard-coded font-size or border-radius px values [PASS]

## Files changed
- `ui/tokens.css` (new) - 60 token definitions
- `ui/app.css` (modified) - all values tokenized via @import + var()
