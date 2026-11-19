# Goal 7: Typography Hierarchy Audit - Re-verified (2026-11-19)
Date: 2026-11-19 | sha12 app.css=bb5828eedd67 tokens.css=56b5c190f9eb

## What was done
Mirror revert had re-introduced off-scale font-size values. This pass re-consolidated all
font-sizes to the 5-step scale and removed off-scale tokens from tokens.css.

### Changes to ui/tokens.css
- Removed: --fs-11 (11px), --fs-13 (13px), --fs-16 (16px)
- Added: --fs-18 (18px), --fs-24 (24px)
- Final scale: --fs-12/14/15/18/24 = 12/14/15/18/24px

### Changes to ui/app.css
All 97 font-size declarations now use on-scale tokens only:
- var(--fs-12) [caption]: 74 uses
- var(--fs-14) [body]: 16 uses
- var(--fs-15) [h3/panel-heading]: 5 uses
- var(--fs-18) [h2/emphasis]: 2 uses

### JS files
All inline font-sizes use var(--fs-12) or are dynamic calculations (components.js SVG text).
0 off-scale values across all ui/*.js files.

## Acceptance test result
**PASS: 0 violations of the 5-step scale.**
- Raw px font-size in app.css: 0
- Off-scale token refs (--fs-11/13/16): 0
- JS inline off-scale values: 0

## Note on prior "closed" evidence
The goal7-typography-audit-closed-2026-11-19.md leaf was correct at the time of writing,
but a mirror revert clobbered the fix. This is the second re-application. The pin file
should be advanced to prevent recurrence (see Goal 8 pin history for the pattern).
