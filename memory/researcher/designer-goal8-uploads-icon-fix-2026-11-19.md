# Designer Goal 8 - uploads.js icon replacement (Researcher assist)

Date: 2026-11-19
Agent: Researcher (assisting Designer goal 8: Icon System)

## What was done
Replaced the warning emoji at L377 in `ui/uploads.js` (gblock span, innerHTML context) with
`UI.iconSized("alert",14)` call. This is the same fix Scribe made previously that was
reverted by a mirror cycle.

## Remaining non-icon emoji in uploads.js
- L109: warning glyph passed to addBubble() - uses esc() so SVG would render as text; needs structural change
- L246: robot emoji default avatar for form field - user content, not UI chrome (OK to keep)
- L341: refresh glyph in a code comment only (not user-facing)
- L367/L447: warning glyph in textContent context - needs innerHTML switch or CSS ::before approach

## Typographic chars (NOT icons - do not replace)
middle-dot, ellipsis, em-dash are standard punctuation, not emoji/icons.

## Verification
grep for warning-glyph in uploads.js now shows 3 occurrences (was 4); the gblock one is gone.
