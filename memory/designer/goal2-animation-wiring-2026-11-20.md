# Goal #2 (Animation/Motion) — wiring progress, 2026-11-20

Parent: memory/goals/designer.md #2 · Sibling leaves: ui/animations.css, ui/app.css, ui/fleet_health.js

## Problem found
`ui/animations.css` existed with 5 keyframes (panel-enter, li-enter, gauge-fill, ring-fill,
notif-slide-in) + a `prefers-reduced-motion` block, but was **never loaded**: app.css only
@imported tokens.css + interactions.css. All classes were dead code (grep across ui/*.js found
zero usages of any animation class).

## Change made this pass
1. `ui/app.css` line 3: added `@import "animations.css";` — the motion layer now loads in the
   portal stylesheet (keyframes + reduced-motion override live).
2. `ui/fleet_health.js` (composite score bar, ~line 85): the fill div now carries class
   `gauge-fill` and sets `--gauge-target:<score>%`. The fleet composite health bar animates
   0 -> score% over 600ms ease-in-out; under prefers-reduced-motion it snaps to final width.
   This is the first real (non-dead) consumer of the animation system.

## Why not closed yet
Goal requires >=4 animations implemented AND reduced-motion + no-layout-shift verified. The 5
animations are implemented and load, but only gauge-fill is applied to a live element; the
panel-enter / li-enter / notif-slide-in classes still have no real consumers in core.js /
notifications.js. Next pass: apply those three to real panel/list/toast elements (and wire
ui/interactions.js into index.html for autoStagger — that file is pinned, needs a pin advance),
then record closure with the ledger.

## Verification commands (re-run next pass)
- `grep -n "animations.css" ui/app.css` -> import present
- `grep -c "@keyframes" ui/animations.css` -> 5
- `grep -n "gauge-fill" ui/fleet_health.js` -> applied to composite bar
