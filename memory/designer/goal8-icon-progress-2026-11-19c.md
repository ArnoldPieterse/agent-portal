# Goal 8 Icon System — progress 2026-11-19 pass c

## Actions taken
1. **Fixed bell icon bug**: `bell` entry was misplaced OUTSIDE the ICONS object (dead code after a return statement in UI.iconSized). Moved it into the ICONS literal. `UI.icon('bell')` now returns the SVG instead of empty string.
2. **Added `dot` icon**: minimal filled circle (`<circle cx=12 cy=12 r=3/>`, fill=currentColor) for use as neutral fallback indicator.
3. **Replaced last raw glyph in rendered JS**: core.js L319 activity timeline fallback `'•'` → `UI.iconSized('dot',8)`. This was the only remaining RAW non-ASCII character in rendered JS output (excluding runtime-replaced index.html buttons).

## Current state
- icons.js: 26 icons defined (was 24, +bell fix +dot), braces balanced, syntax clean.
- core.js: 12 UI.icon refs (was 11), 0 raw non-ASCII symbols in rendered content. The single `→` at L449 is inline sentence text ("moved X → TODO_completed.md"), not an icon position — acceptable typography.
- uploads.js: 0 raw non-ASCII symbols (the ↻ at L326 is inside a code comment, never rendered).
- index.html: 3 glyph buttons (↺/↻/↻) are runtime-replaced by the DOMContentLoaded IIFE in core.js (replaceBtnGlyph ×3).

## Remaining for full closure
- Verifier's caution noted "48 non-ASCII glyph chars" from an earlier audit. Current count of RAW non-ASCII in rendered JS = 1 (the → arrow, which is inline text not icon). The \uXXXX escape sequences (68 at HEAD) are code-level escapes per established convention.
- To fully satisfy "used consistently across panels": uploads.js has 0 UI.icon call-sites. Adding one (e.g., a folder icon in the files panel header or an upload icon in queue items) would close this criterion.
- Browser render acceptance still blocked by pale-sandbox wall (blockers.md L89).

## Files modified
- ui/icons.js (bell moved into ICONS, dot added)
- ui/core.js (L319 fallback → UI.iconSized('dot',8))
