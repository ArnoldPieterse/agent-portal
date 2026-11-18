# Design Token Audit & Gap Closure - EVIDENCE

Date: 2026-11-18
Goal: #1 (Design token audit & gap closure)

## What was done
Grepped all ui/ files (app.css, core.js, uploads.js) for hard-coded color values
(hex + rgba) outside the :root token block. Found 36 hex colors in app.css,
10 rgba() values in app.css, and 8 hex colors across JS files.

## Actions taken
1. Added 43 new design tokens to :root in ui/app.css (semantic names for every
   previously hard-coded color: --bg-chat, --bg-popup, --bg-sel, --link-fleet,
   --spinner-arc, --dot-busy, --warn-amber, --err-red, --shadow-1..4, etc.)
2. Replaced all 36 hex colors in app.css with var(--token) references.
3. Replaced all 10 rgba() values in app.css with var(--token) references.
4. Replaced all 8 hex color literals in core.js and uploads.js with var(--token)
   references (inline styles now use CSS custom properties).

## Verification
- grep for hex colors in ui/app.css outside :root: 0 hits [PASS]
- All 60 var() references in app.css resolve to defined tokens [PASS]
- All 4 var() refs in core.js resolve [PASS]
- All 12 var() refs in uploads.js resolve [PASS]
- Total token count: 66 (was 23 before this pass)

## Files changed
- ui/app.css (24,406 bytes; was 22,585)
- ui/core.js (29,133 bytes)
- ui/uploads.js (34,762 bytes)

## Note
Total CSS+JS transfer is now 86.2 KB (was ~80 KB pre-tokenization). The token
overhead (~2KB for :root declarations) will be addressed in Goal #3 (CSS bundle
performance budget) via minification.
