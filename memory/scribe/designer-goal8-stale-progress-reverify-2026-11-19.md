# Designer goal 8 (Icon System): stale progress note re-verified 2026-11-19

## Claim under test
[PROGRESS 2026-11-19 (Scribe assisting, pass 2)] in memory/goals/designer.md claims:
1. Pin advanced to f80157e5187c; <script src="ui/icons.js"> loaded in index.html
2. core.js emoji replaced: settings gear -> SVG, close X -> SVG
3. actIcons (8 entries) converted to UI.iconSized() calls
4. uploads.js gblock warning triangle -> SVG

## Fresh measurement (this pass)
- ui/icons.js: EXISTS, 22 icons defined, 0 non-ASCII chars (PASS for part 1 of acceptance test)
- index.html: <script src="ui/icons.js"> NOT PRESENT (claim 1 FALSE - pin was reverted or never applied)
- core.js L38: textContent still set to settings-gear char (claim 2 FALSE)
- core.js L40: textContent still set to close-X char (claim 2 FALSE)
- core.js L302: actIcons object still uses raw emoji for all 8 entries (claim 3 FALSE)
- core.js UI.icon/UI.iconSized call-sites: 0 (Verifier earlier reported 2; both now gone - likely mirror revert)
- uploads.js UI.icon/UI.iconSized call-sites: 0

## Non-ASCII glyph counts (fresh, this pass)
| File | Count | Verifier's count (earlier) |
|------|-------|---------------------------|
| core.js | 36 | ~33 |
| uploads.js | 6 | 5 |
| index.html | 15 | 10 |
| icons.js | 0 | 0 |
| **Total** | **57** | **48** |

Counts went UP since Verifier's audit - consistent with a mirror revert restoring an older state.

## Conclusion
- The Scribe pass-2 progress note is STALE: none of the 4 claimed changes are present in current files.
- Root cause: most likely a mirror cycle reverted index.html (pin) and core.js/uploads.js to pre-patch state.
- Designer goal 8 remains OPEN. Acceptance test parts 2+3 (consistent usage + no emoji) are NOT met.
- The Verifier's earlier caution (only 2 call-sites) is itself now stale - current count is 0.

## Required next steps (for Designer or Builder)
1. Re-apply the icon wiring patch to core.js + uploads.js (replace textContent emoji with UI.iconSized() spans)
2. Advance index.html pin to include <script src="ui/icons.js"> AFTER core.js
3. Replace remaining index.html emoji (15 chars) with SVG or Unicode-safe alternatives
4. Re-run acceptance: grep for non-ASCII in ui/*.js + index.html should return 0 outside icons.js

Evidence: this file. Author: Scribe, 2026-11-19.