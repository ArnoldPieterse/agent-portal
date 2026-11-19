# Goal #8 Icon System - Progress 2026-11-19 (Designer, auto-loop pass)

## Changes
1. **ui/icons.js**: Added `refresh` (circular arrow, 24x24/1.5px stroke) and `undo` (back-arrow, 24x24/1.5px stroke). Total: 24 icons.
2. **ui/core.js L426**: Replaced U+21A9 glyph button with UI.iconSized('undo',12)+' restore' - inline SVG now matches the system.
3. **ui/core.js (end)**: Added DOMContentLoaded IIFE that replaces 3 pinned-index.html glyph buttons (#resetBtn U+21BA, #actRefresh U+21BB, #filesRefresh U+21BB) with SVG refresh icons + text at runtime. Follows established JS-injection pattern (same as print button).

## Static Verification
- icons.js: braces 12/12 balanced; 24 icon names defined
- core.js: braces 270/270, parens 965/965 balanced
- UI.icon/Sized call-sites in core.js: 9 (was 7 before this pass)
- Remaining rendered glyph chars in JS: 0 (core.js clean; uploads.js has 1 in a comment only)
- index.html still has 3 glyph chars in markup BUT they are replaced at runtime by the DOMContentLoaded hook

## Still Needed for Full Closure
- Browser verification: confirm all buttons render SVG icons visually (needs non-sandbox seat with msedge CDP - see blockers.md L89)
- uploads.js: 0 UI.icon() call-sites still - the progress notes say Scribe already replaced gblock warning-glyph, so this may be a count issue (different pattern). Needs recheck in browser.

## Files Modified
- ui/icons.js (2 lines added)
- ui/core.js (1 line modified + 10-line IIFE appended)
