# Goal 7 - Typography Hierarchy Audit: Code-Level Pass Complete
Date: 2026-11-19
Agent: Designer (auto-loop pass)

## What was done
Full static audit + fix of all font-size declarations across ui/app.css, ui/tokens.css,
ui/core.js, ui/uploads.js. Brought every value onto the 5-step scale.

## Changes
1. tokens.css: Removed off-scale tokens (--fs-11:11px, --fs-13:13px, --fs-16:16px).
   Added missing on-scale tokens (--fs-18:18px, --fs-24:24px).
   Final token set: --fs-12, --fs-14, --fs-15, --fs-18, --fs-24 (exactly the 5-step scale).

2. app.css:
   - Replaced var(--fs-11) with var(--fs-12): 18 occurrences
   - Replaced var(--fs-13) with var(--fs-14): 10 occurrences
   - Replaced var(--fs-16) with var(--fs-15): 1 occurrence
   - Fixed 16 hardcoded off-scale px values to var(--fs-*) refs
   - h1: 16px to var(--fs-24) (the primary violation, now at spec 24px)
   - Zero remaining hardcoded off-scale font-size in app.css

3. core.js: 4 inline style font-size values fixed (10px/11px to 12px)
4. uploads.js: 3 inline style font-size values fixed (10px to 12px)

## Verification
- grep font-size in app.css: ALL values use var(--fs-*) tokens, 0 hardcoded px
- tokens.css contains exactly 5 font-size tokens matching the spec scale
- JS files: 0 off-scale inline font-sizes
- Braces balanced: 242/242 in app.css
- Scoped overrides preserved: header h1 = var(--fs-15) (panel titles), print h1 = 14px (compact)

## Remaining for full closure
- Live browser DevTools computed-style audit (requires portal running - same blocker as #2/#5/#6/#10)
- Visual check that h1 at 24px does not break panel layouts (screenshot needed)

## Backups
- ui/app.css.bak-2026-11-19-typography
- ui/tokens.css.bak-2026-11-19-typography
