# Cockpit P0+P1 UX Fixes — 2026-11-23 (Designer)

Fixed in ui/cockpit.js (5 edits, braces balanced 65/65):

## P0 — Circuit-breaker visual prominence
- Added .ck-host-critical CSS: 3px red left-border + ckpulse keyframe animation (1.2s ease-in-out infinite, opacity 1→0.55)
- Host row div now gets class ck-host-critical when x.circuit is truthy
- Circuit state text now bold (font-weight:700) for stronger contrast at small size
- Reference pattern: Grafana alert-panel border+subtle-pulse

## P1 — Keyboard access (WCAG 2.1 SC 2.1.1)
- Escape key closes panel (keydown listener on document)
- btn gets aria-expanded + aria-controls attributes
- aria-expanded toggles with panel open/close state

## P2 — Loading skeleton
- .ck-skel overlay div (position:absolute, z-index:2, centered text) inserted as first child of panel
- render() removes #ckpSkel on first successful data fetch
- Eliminates blank-section flash during initial fetch

## Verification
- Brace balance check: 65 open / 65 close = balanced
- All new CSS in the css() array with proper comma delimiters
- No console errors expected (all DOM ops guarded, optional chaining on skeleton removal)
