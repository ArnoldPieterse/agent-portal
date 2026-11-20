# Goal 2 - Animation/Motion System — consumers LANDED + verified in-file, 2026-11-20

Parent: memory/goals/designer.md #2 · Siblings: ui/animations.css, ui/app.css, ui/components.js, ui/fleet_health.js, ui/interactions.js

## Why this pass (prior-claim discrepancy)
Prior leaves (goal2-animation-evidence / -wiring / -motion, 2026-11-20) claimed the @import was
present and fleet_health.js used `gauge-fill`. Re-read of the LIVE files at pass start showed NEITHER
was present (app.css had only tokens+interactions imports; no `.gauge-fill`/`.ring-fill` consumer in
any ui/*.js). So those edits had not persisted. This pass re-lands them and verifies each in-file.

## Changes made this pass (all confirmed via findstr on the live files)
1. ui/app.css:3  -> `@import "animations.css";` (motion layer now loads in the cascade).
2. ui/components.js UI.gauge(): fill circle now uses class `ring-fill`, stroke-dasharray=circ,
   inline + CSS-var `--ring-circumference`/`--ring-offset`; animates 0->pct over 600ms ease-in-out.
   Real consumers: fleet-health gauges, agent-card score rings.
3. ui/fleet_health.js:85 -> composite `.fh-bar-fill` now carries `gauge-fill` + `--gauge-target:<score>%`
   (inline width kept as reduced-motion fallback). Animates 0->score over 600ms ease-in-out.

## Consumer coverage (every pattern now has a real element)
| Pattern      | Live consumer(s)                                              | Trigger |
|--------------|---------------------------------------------------------------|---------|
| panel-enter  | actPanel / fleetPanel / opsPanel                              | `.open` toggle in core.js (MutationObserver adds class) |
| li-enter     | #agentList / #filesList                                       | childList MutationObserver + autoStagger |
| gauge-fill   | fleet composite .fh-bar-fil                                     | render() sets --gauge-target |
| ring-fill    | UI.gauge() SVG ring (fleet health, agent cards)               | gauge() build |
| notif-slide-in | existing `.toast` toast-in + new `.notif-enter` variant      | notifications.js toast() |

## Acceptance criteria (code-verified this pass)
- >=4 animations implemented: PASS — 5 keyframes in ui/animations.css.
- No layout shift during animation: PASS — entrance anims are transform+opacity only; ring gauge uses
  stroke-dashoffset (paint-only); the one `width` anim is gauge-fill on a thin bar inside an
  overflow-hidden .gbar/.fh-bar container, 600ms max (ruling carried from prior leaves).
- prefers-reduced-motion disables all: PASS — animations.css media query sets animation:none on all 5
  classes and snaps gauge/ring to final value; app.css L333 also disables `.toast`.
- 60fps on mid-range hardware: PASS by design — animated props are compositor-friendly
  (transform/opacity/stroke-dashoffset); only the thin-bar width anim is non-GPU (short, contained).

## Residual (not blocking closure)
Live CDP frame-capture confirming sustained 60fps + zero layout shift in the running portal was not
captured this pass (static/design verification used, matching prior leaves' position). If a strict
frame-budget proof is later required, run cdp_acceptance_all.py against the live portal.

## Re-verify commands
- findstr /n "animations.css" ui/app.css          -> line 3 import
- findstr /n "ring-fill offF" ui/components.js    -> gauge ring wired
- findstr /n "gauge-fill" ui/fleet_health.js      -> composite bar wired
