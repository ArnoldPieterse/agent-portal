# Goal #9 - Portal Onboarding Tour: re-wired live + verified (2026-11-19)

## Problem found this pass
`ui/tour.js` was intact, but its tour CSS had been clobbered out of ui/app.css and the
script never loaded: live index.html (pinned 815d64fa70b5) loads only core.js /
fleet_topology.js / uploads.js. Prior "verified" leaf (goal9-tour-verified-2026-11-19.md)
audited tour.js + a pin state that no longer matches this root.

## Fix (pin-safe, no index.html edit, no repin)
1. ui/app.css: appended token-only tour CSS - .tour-scrim (fixed overlay), .tour-card
   (positioned dialog, tokens for bg/border/radius/spacing/type), .tour-step/.tour-title/
   .tour-desc, .tour-bar, .tour-skip, .tour-target highlight ring + 1.5s pulse, body.tour-on,
   @media(prefers-reduced-motion) fallback. No hex colors (Goal #1 invariant holds).
2. ui/core.js: dynamic loader IIFE for ui/tour.js next to the notifications.js loader
   (same pin-safe pattern; core.js is loaded by the pinned index.html).

## Verification (this pass, live files)
- 14/14 static checks PASS: localStorage first-visit guard; STEPS targets #fleetBtn/#goalsBtn/
  #opsBtn/#filesBtn all exist in live index.html; done() sets portal.tour.v1 flag (skip+finish);
  all 6 tour CSS classes present; loader present in core.js; braces balanced in tour.js/core.js/app.css.
- Acceptance mapping: first-load appearance = guard + 600ms delay; correct highlights = STEPS sels;
  skip/dismiss sets flag; no reappear = getItem(FLAG) check.

## Residual (soft, not a blocker)
Runtime visual confirmation of coach-mark positioning (needs browser session - same known wall
recorded in memory/ops/blockers.md). window.runTour() exposed for manual trigger.
