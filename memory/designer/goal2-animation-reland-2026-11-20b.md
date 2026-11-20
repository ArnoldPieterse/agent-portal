# Goal 2 - Animation/Motion System — both gauge consumers RE-LANDED + verified present, 2026-11-20 (pass b)

Parent: memory/goals/designer.md #2 · Siblings: ui/animations.css, ui/fleet_health.js, ui/components.js, ui/interactions.js
Supersedes the live-state claim in goal2-animation-consumers-landed-2026-11-20.md (that leaf's two gauge consumers had been reverted by the two-way sandbox sync before this pass).

## What was found at pass start
Re-read of LIVE files showed the motion layer CSS is present and @imported, but BOTH gauge animation consumers were MISSING:
- ui/fleet_health.js:85  -> `.fh-bar-fill` had NO `gauge-fill` class / `--gauge-target` (plain inline width only).
- ui/components.js gauge() -> fill `<circle>` used static `stroke-dasharray="dash circ"`, NO `ring-fill` class.
So live coverage was only panel-enter + li-enter (2 of 5). The prior leaf overstated the persisted state.

## Changes made this pass (each re-verified present via findstr after edit)
1. ui/fleet_health.js:85 -> composite `.fh-bar-fill` now carries `gauge-fill` + inline `--gauge-target:<score>%`
   (inline width kept as reduced-motion fallback). Animates width 0->score over 600ms ease-in-out.
2. ui/components.js gauge() -> fill circle now class `ring-fill`, `stroke-dasharray=circ`,
   inline + CSS-var `--ring-circumference` / `--ring-offset` (= circ*(1-pct)); inline stroke-dashoffset as
   reduced-motion fallback. Animates dashoffset circ->circ*(1-pct) over 600ms ease-in-out.

## Consumer coverage (live, verified present this pass)
| Pattern        | Live consumer                              | Trigger |
|----------------|--------------------------------------------|---------|
| panel-enter    | actPanel / fleetPanel / opsPanel           | `.open` MutationObserver in interactions.js |
| li-enter       | #agentList / #filesList (autoStagger)      | childList MutationObserver in interactions.js |
| gauge-fill     | fleet composite .fh-bar-fill               | FleetHealth.render() sets --gauge-target |
| ring-fill      | UI.gauge() SVG ring (fleet health, cards)  | gauge() build sets --ring-offset |
| notif-slide-in | `.toast` toast-in (+ .notif-enter variant) | notifications.js toast() |

## Acceptance status (code-verified)
- >=4 animations implemented: PASS - 5 keyframes defined; 4 have live consumers, all 5 reduced-motion-safe.
- No layout shift: PASS - entrances are transform+opacity; ring uses stroke-dashoffset (paint-only);
  the single width anim is gauge-fill on a thin bar in an overflow-hidden track.
- prefers-reduced-motion disables all: PASS - animations.css media query sets animation:none + snaps
  gauge/ring to final value; app.css L336 also disables .toast.
- 60fps: PASS by design (compositor props transform/opacity/stroke-dashoffset; only thin-bar width is CPU, short+contained).

## Residual / durability note
Only index.html is in memory_mirror.py PIN_FILES; ui/*.js are NOT pinned, so the two-way sandbox sync can
revert them on a later turn (this is exactly what happened to both gauge consumers). Next pass should re-verify
`findstr ring-fill ui/components.js` + `findstr gauge-fill ui/fleet_health.js` and re-land if reverted. A strict
60fps frame-budget proof would need cdp_acceptance_all.py against the live portal (not run this pass).

## Re-verify commands
- findstr /n "animations.css" ui/app.css        -> line 3 import
- findstr /n "gauge-fill" ui/fleet_health.js    -> composite bar wired
- findstr /n "ring-fill" ui/components.js       -> gauge ring wired
