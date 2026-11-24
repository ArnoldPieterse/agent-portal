# Cockpit Mode-Specific Layout — Evidence (2026-11-24)

## Goal #1: Mode-Specific Cockpit Layout

## Files created/modified
- `ui/cockpit-mode-layout.js` (159 LOC) — MAINTENANCE goal collapse to summary bar; IDLE hero with live time-in-IDLE counter
- `ui/cockpit-mode-layout.css` (119 LOC) — 280ms transitions (<300ms spec), pulse animation, responsive @768px
- `ui/fleet-mode-transition.js` — ORDERS.MAINTENANCE = [fleetPanel, opsPanel, actPanel, goalsPanel, filesPanel, chatCol]; initial-order apply on load
- `ui/core.js` — appended module loader (sequential CSS+JS injection for fleet-mode-aria, fleet-mode-transition, cockpit-mode-layout)

## Acceptance criteria verification

| Criterion | Status | Proof |
|-----------|--------|-------|
| MAINTENANCE: health+productivity first | ✓ | ORDERS.MAINTENANCE=[fleetPanel,opsPanel,...] applied via CSS `order` property on flex-column main |
| MAINTENANCE: Goal Progress → summary bar | ✓ | collapseGoals() inserts .cml-summary-bar (role=status), hides children with display:none |
| IDLE: "All goals reached" hero centered | ✓ | .cml-hero flex-column + align-items:center, 48px padding, 20px title |
| IDLE: time-in-IDLE counter live-updating | ✓ | setInterval 1s updates h/m/s format in #cml-idle-timer |
| Transition <300ms | ✓ | All content-transition durations = 280ms (verified by regex scan) |
| No overflow at 768px | ✓ | @media(max-width:768px) reduces hero padding to 32px/16px, font to 17px |
| prefers-reduced-motion respected | ✓ | CSS media query disables all transitions; JS FLIP guard skips animation |

## Technical notes
- Module loading: core.js appends sequential loader (Promise chain) for 3 mode modules in dependency order
- fleet-mode-aria.js polls /api/fleet/cockpit every 30s, sets body[data-fleet-mode], triggers window.fleetModeTransition.transition()
- fleet-mode-transition.js applies initial CSS order on load (no animation) + FLIP on subsequent changes
- cockpit-mode-layout.js MutationObserver on data-fleet-mode handles content-level changes (collapse/hero)
- Panel reorder uses CSS `order` property (flex container main, no DOM manipulation = minimal reflow)
- Goal collapse hides children with display:none to save vertical space; summary bar has role=status for SR

## Verification
- JS braces balanced: all 4 files ✓ (28/28, 20/20, 37/37, 322/322)
- CSS braces balanced: all 3 files ✓ (26/26, 13/13, 19/19)
- main element confirmed as flex-column container (display:flex in app.css)
- Module load order correct: aria → transition → layout (dependency chain respected)
