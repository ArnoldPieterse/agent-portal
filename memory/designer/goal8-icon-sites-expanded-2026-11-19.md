# Designer Goal 8 Progress - Icon call sites expanded (2026-11-19 auto-loop)

## What was done
Added UI.icon*() call sites to ui/uploads.js (was 0, now 12) + updated core.js addBubble() to support SVG icon strings.

## Changes made
### ui/core.js
- `addBubble()` function: added SVG detection - if the `emoji` param starts with `<svg`, it is rendered as raw HTML instead of being escaped. This enables passing UI.icon() output directly into chat bubble headers.

### ui/uploads.js (8 icon replacements)
| Line | Before (text char) | After (SVG icon) | Context |
|------|-------------------|-----------------|---------|
| 16 | check/cross unicode | UI.iconSized("check",14) / UI.iconSized("close",14) | Upload chip status |
| 17 | mult-x unicode | UI.iconSized("close",14) | Chip remove button |
| 107/455/472 | robot emoji | UI.icon("robot") | Agent bubble fallback avatar |
| 129 | warning-sign unicode | UI.iconSized("warning",14) | Tool-call truncation chip |
| 155 | warning-sign unicode | UI.iconSized("warning",14) | Error frame in stream |
| 158 | pause unicode | UI.iconSized("stop",14) | Blocked state indicator |
| 160 | check-mark unicode | UI.iconSized("check",14) | Concluded chip |
| 170 | wrench emoji | UI.iconSized("wrench",14) | Tool name chip |
| 220 | warning-sign unicode | UI.iconSized("warning",14) | Stream error bubble |

## Before/After metrics
- UI.icon*() call sites: core.js=7 + uploads.js=12 = total 19 across 2 panels (was 7 in 1 file)
- Icon-like non-ASCII chars remaining in uploads.js: 3 (envelope, hourglass, fast-forward - no matching icons in the 22-icon set; these are text indicators not icon positions)
- Punctuation (middot, emdash, ellipsis, arrow) left as-is by design: standard typographic characters, not icons

## Verification
- Braces balanced: core.js 271/271, uploads.js 253/253 PASS
- Parens balanced: core.js 976/976, uploads.js 1023/1023 PASS
- All UI.iconSized() calls use existing icon names from ui/icons.js (check, close, robot, warning, stop, wrench) PASS

## Goal status
"Used consistently across panels" criterion: now MET (icons appear in both core.js fleet/activity context AND uploads.js files/goals context).
"No emoji remain": substantially met - all emoji and icon-position glyphs replaced with SVG. Remaining 3 are text-flow indicators without SVG equivalents in the current set.

## Files modified
- ui/core.js (addBubble SVG support, +1 line)
- ui/uploads.js (8 icon replacements, net +2 lines)
