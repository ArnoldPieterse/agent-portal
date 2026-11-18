# Goal #9: Onboarding Tour - CSS Re-landed (20611-19)

## Context
tour.js (4591 bytes) was present and syntactically valid but ALL tour CSS classes were missing from app.css (clobbered by mirror revert). Tour would have rendered as unstyled positioned divs.

## What was done this pass
Added 9 tour CSS rules to ui/app.css:
- body.tour-on (overflow lock)
- .tour-scrim (full-viewport overlay, z-index 10000)
- .tour-card (positioned card, panel bg, shadow, animation)
- .tour-step / .tour-title / .tour-desc (text hierarchy)
- .tour-bar (flex row for buttons)
- .tour-skip (ghost button style)
- .tour-target (accent outline on highlighted element)

All values use design tokens (var(--sp-*), var(--fs-*), var(--br-*), var(--lh-base)).

## Verification (static)
- tour.js: braces 21/21, parens 80/80 - balanced
- Class name parity: all 9 classes used by tour.js now have matching CSS rules
- Token resolution: all var() refs in new CSS resolve to defined tokens
- No index.html edit needed (tour.js already loaded via script tag)
- localStorage flag logic present and correct in tour.js

## Acceptance status
| Criterion | Static | Live |
|-----------|--------|------|
| Tour appears on first load (no flag) | PASS (code path verified) | CDP-gated |
| Steps highlight correct elements | PASS (selectors match DOM ids) | CDP-gated |
| Skipping/dismissing sets flag | PASS (localStorage.setItem in done()) | CDP-gated |
| Does not reappear | PASS (flag check before start) | CDP-gated |

## Files touched
ui/app.css (+12 lines tour styles)
