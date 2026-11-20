# Goal #4 (Responsive 768px) — sub-44px touch-target defect fixed + verifier made honest
Date: 2026-11-21. Status: PROGRESS (not closure). Live CDP measurement still pending portal-up on :8099.

## What was wrong
The 768px icon-rail block (ui/app.css) shipped with genuine sub-44px touch targets, violating the
acceptance criterion "touch targets >=44px":
- `.ah button` (#addAgent) = 32x32
- `.acard button` (per-card edit/delete) = 28x28 (two of them)
The prior `goal4_768_verify.py --static` also FALSE-failed A/B/C on stale expectations
(assumed aside==64px, inline flex-direction:row, and didn't match the actual design), so it could
never go green even when the CSS was right.

## Fix (ui/app.css @media max-width:768px)
Moved to TRUE icon-rail mode so only >=44px interactive targets remain:
1. `.acard button{display:none}` — hide per-card micro-actions in rail mode (card itself is the tap
target; actions reachable via editor/chat). Removes both 28px sub-44 targets.
2. `.acard{...min-height:44px}` — card tap target >=44px.
3. `.ah button` -> 44x44 (line-height 44) — header add-agent control tappable, fits 56px rail.
`.em` (emoji glyph, 32px box) is a non-interactive span inside the card — not a touch target.

## Verifier alignment (memory/designer/goal4_768_verify.py)
Made both modes measure the SAME truth so neither false-fails:
- static A: require `#fleetBody` overflow-x:auto (dropped spurious inline flex-direction:row).
- static B: rail = aside width <=64px (was hardcoded ==64; CSS uses 56px).
- static C: `.acard .nm{display:none}` AND `.acard button{display:none}` (matches real design).
- static D: flag only INTERACTIVE selectors (button/#send/#attach/input/[role=button]), treat
  min-width/min-height as satisfying, exempt display:none — mirrors the live CDP element set.
  (removes the false-positive on the `.em` span)
- live B: `asideW <= 64` (was `== 64`).

## Measured result (this pass)
`python memory/designer/goal4_768_verify.py --static` -> ALL PASS:
A_fleet_horizontal_scroller PASS, B_sidebar_icon_rail PASS, C_chat_full_width_text_hidden PASS,
D_no_explicit_sub44_touch_targets PASS. Artifact: memory/designer/breakpoint-evidence/goal4-768-static-2026-11-21.json
CSS brace balance 333/333.

## Remaining for closure (honest — NOT done)
Live acceptance measurement at 768px via `python memory/designer/goal4_768_verify.py` (CDP mode):
needs portal serving on http://127.0.0.1:8099 (was DOWN this pass; portal lifecycle = Mechanic's
lane / schtask PortalRun). Confirms: no page-level hscroll, rail renders <=64px, #fleetBody is the
horizontal scroller, and every visible interactive element >=44px. Once portal is up, run CDP mode,
capture JSON+screenshot, then record closure via goal_ledger with that artifact.
