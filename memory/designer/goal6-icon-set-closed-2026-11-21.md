# Goal 6 (SVG Icon Set) — Closure Evidence
Date: 2026-11-21. Owner: Designer.

## What was wrong
`memory/designer/icon-set.md` claimed a 28-icon inventory, but `ui/icons.js` only defined 24.
The four required-minimum icons **host, model, error, loading** were absent, so:
- `UI.iconSized('host',16)` (used by `ui/panel-icons.js` for the fleet panel header) returned
  an empty string → blank header icon.
- The goal's own acceptance list named these four as required; spec and code disagreed.

## Fix
Added `host`, `model`, `error`, `loading` to the `ICONS` object in `ui/icons.js`
(standard attrs: viewBox 0 0 24 24, fill none, stroke currentColor, stroke-width 1.5,
round caps/joins). Now 28/28 icons defined; spec and implementation match.

## Acceptance criteria — all PASS (verified by regex/structural check on ui/icons.js)
| Criterion | Result |
|-----------|--------|
| >=10 icons defined | 28 defined |
| All 10 required-minimum present | agent, host, model, alert, check, error, loading, search, settings, close — all resolve |
| All use currentColor | PASS (no hardcoded fills; only fill="none") |
| No external font dependencies | PASS (no <img>, no font refs) |
| Scale at 16/24/32px | PASS (UI.iconSized injects width/height; viewBox scales stroke proportionally) |

## Emoji / text-indicator replacement
Scanned index.html + all ui/*.js and ui/*.css for emoji/glyph ranges. The only matches are
arrow characters in **comments** and one inline status sentence (`core.js:449` "→ TODO_completed.md").
No user-visible status *indicator* remains text/emoji-based — the UI uses `UI.icon()` /
`UI.iconSized()` + `ui/panel-icons.js`. Replacement objective satisfied.

## Artifacts
- ui/icons.js (28 icons; 4 added)
- memory/designer/icon-set.md (spec, changelog updated)
- This leaf
