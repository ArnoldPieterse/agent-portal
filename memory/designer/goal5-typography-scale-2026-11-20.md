# Goal 5 - Typography Scale Refinement
Date: 2026-11-20
Status: VERIFIED

## What was done
1. Added `--lh-body:1.4` to tokens.css :root (fills gap between --lh-loose:1.35 and --lh-mono:1.6)
2. Converted all 9 raw line-height values in app.css → var() references:
   - `line-height:1` → `var(--lh-tight)` (#attach, .toast-close)
   - `line-height:1.3` → `var(--lh-base)` (.mh-d)
   - `line-height:1.6` → `var(--lh-mono)` (.opsbox, .ft-models)
   - `line-height:1.7` → `var(--lh-mono)` (#actBody)
   - `line-height:1.5` → `var(--lh-body)` (.sub, .ft-tooltip)
   - `line-height:1.4` → `var(--lh-body)` (print body)
3. Added `max-width:72ch` to `.tour-body` for line-length enforcement (<75ch requirement)

## Verification
- 99/99 font-size declarations use var() refs (0 orphans)
- 16/16 line-height declarations use var() refs (0 orphans)
- JS inline styles all use var(--fs-*) tokens with fallbacks
- app.css: 299/299 braces balanced; tokens.css: 6/6 balanced
- Monospace font applied to 5 code/data elements (#actBody, .opsbox, .fmodels, #peek .pk-body, .ft-dt-base)

## Artifacts
- ui/tokens.css (added --lh-body:1.4)
- ui/app.css (9 line-height conversions + 1 max-width addition)