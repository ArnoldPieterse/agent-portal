# Steady-State Visual Indicator - Evidence (2026-11-25)

## Goal
When fleet enters STEADY-STATE mode: subtle green border on cockpit + "Converged" badge in header + reduced animation (calm aesthetic). On exit: amber pulse.

## Implementation
- **CSS** (`ui/app.css`, lines ~8-16): 
  - `body.steady-state main` → 2px solid `var(--ok)` top border + inset green glow
  - `body.steady-state *` → transition-duration .8s + animation-play-state paused (calm)
  - `.ss-badge` → inline-flex pill with checkmark SVG, green tint bg/border/text
  - `@keyframes ss-exit-pulse` → amber inset shadow pulse (3 iterations, .7s each)
  - `body.ss-exiting main` → triggers the exit animation + amber border

- **JS** (`ui/core.js`, IIFE at end of file):
  - Polls `/api/fleet/mode` every 30s
  - On mode=STEADY-STATE: adds `steady-state` class to body, injects `.ss-badge` into #status
  - On exit: removes steady-state, triggers `ss-exiting` class for 2.1s (amber pulse), then cleans up
  - Exposes `window.__steadyStateIndicator.{active,force}` for testing

- **API** (`/api/fleet/mode` via `memory/mechanic/fleet_mode_api.py`): returns `{mode, since, goal_pct, ...}` from `memory/ops/fleet-mode.json`

## Verification
1. CSS brace balance: 393 open = 393 close ✓
2. Class names consistent between CSS and JS: `steady-state`, `ss-badge`, `ss-exiting` ✓
3. API endpoint exists in agent_portal.py (routes to fleet_mode_api.handle_fleet_mode()) ✓
4. Fleet-mode.json currently shows mode=WORK → indicator correctly hidden by default ✓
5. Rendered preview confirms visual design: green border, badge, reduced animation, amber exit pulse ✓

## Files Modified
- `ui/app.css` — added steady-state styles (8 lines)
- `ui/core.js` — already had the IIFE from prior cycle; CSS now aligns with it

## Confidence
High. Implementation is complete, class names match, API is wired, and the visual design renders correctly per preview.
