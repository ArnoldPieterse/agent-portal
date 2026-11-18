# Goal #2 Fleet Panel - Responsive Breakpoints Re-landed (2026-11-18 ~05:3x)

## Problem found
Prior passes added @media(min-width:1024px) and @media(min-width:1920px) rules for the fleet panel,
but they were reverted by the mirror cycle (ui/app.css is not pinned like index.html). The live CSS
had NO min-width breakpoints - only max-width:768px and max-width:375px.

Also: --sp-32 token was missing from :root (used by the responsive rules but never defined),
causing padding to fall back to initial/0.

## Fix applied this pass
1. Added --sp-32:32px to :root token layer (line 7)
2. Added @media(min-width:1024px) block:
   - #fleetPanel padding: var(--sp-16) var(--sp-32)
   - #fleetHead flex row with space-between
   - #fleetTopo max-width:960px centered
   - .ft-detail width:260px (wider on larger screens)
3. Added @media(min-width:1920px) block:
   - #fleetPanel padding: var(--sp-32) var(--sp-32)
   - #fleetTopo max-width:1100px centered
   - .ft-detail width:280px, font-size:13px
   - .ft-tooltip max-width:280px, font-size:12.5px

## Verification
- Braces balanced: 266/266
- All 23 var() references have matching :root definitions (0 missing)
- Both min-width breakpoints confirmed present in live CSS
- File size: 24469 bytes, 297 lines
- sha12: 83d9b2cb0ffc

## Goal #2 acceptance criteria status
- [x] Loading state: .ft-skeleton with pulsing bars (implemented)
- [x] Error state: .ft-banner-error with retry logic in fleet_topology.js
- [x] Empty state: .ft-banner-empty + .ft-empty-label (implemented)
- [x] Responsive at 1024px and 1920px: breakpoints NOW present in live CSS
- [~] No layout breakage: programmatic verification passed prior passes; browser screenshot still blocked (NEEDS-HUMAN in memory/ops/blockers.md)

## Note on mirror reverts
ui/app.css is NOT pinned (only index.html is). Any changes to ui/app.css will be reverted on the
next mirror cycle unless:
- The change is also committed to git AND the mirror source has it, OR
- A human advances the pin for app.css (not currently supported)

This means fleet panel responsive rules may need re-landing after each mirror cycle.
Recommendation: add ui/app.css to PIN_FILES in memory_mirror.py with its own sha12.
