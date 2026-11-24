# Fleet Mode ARIA + Keyboard Nav - Evidence
Date: 2026-11-24
Goal: Designer #1

## What was implemented
1. **ARIA-live region** (`#fleetModeLive`): Created dynamically in `ui/core.js` (line ~606+).
   - `aria-live="assertive"` + `role="alert"` for immediate screen reader announcement
   - Visually hidden via clip-rect pattern (WCAG 2.1 compliant)
   - Announces "Fleet entered work/maintenance/idle mode" on transition

2. **Keyboard navigability** for all 5 cockpit panels:
   - `role="region"` + `aria-label` added to each panel div
   - `tabindex="-1"` enables programmatic focus (WCAG pattern)
   - `aria-hidden` toggled with open/closed state
   - Focus moves INTO panel on open, RETURNS to toggle button on close
   - CSS focus ring: 2px solid accent color, visible on keyboard focus

3. **Mode polling + body class theming**:
   - Polls `/api/fleet/mode` (with fallback to `/api/fleet.fleet_mode`) every 10s
   - Sets `body.fleet-work` / `.fleet-maintenance` / `.fleet-idle` classes
   - CSS: header border-bottom color shifts green/amber/grey per mode

## Files changed
- `ui/core.js`: +56 lines (ARIA IIFE appended after keyboard shortcuts)
- `ui/app.css`: +10 lines (mode theming + focus ring styles)

## Verification
- Bracket balance verified: 0 diff on all three bracket types
- Code follows existing patterns in file (IIFE, $() helper, requestAnimationFrame for DOM timing)
- ARIA pattern matches WCAG 2.1 SC 4.1.3 (Status Messages) + SC 2.1.1 (Keyboard)
