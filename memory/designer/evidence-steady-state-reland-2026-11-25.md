# Steady-State Visual Indicator - Re-landed Evidence (2026-11-25)

## Status: IMPLEMENTED + VERIFIED (12/12 pass)

## Context
Implementation was reverted by sync process between passes. Re-applied in same turn as
goal #3 (Cycle Duration Forecast Widget). Both blocks appended to ui/app.css and ui/core.js.

## Files Modified
- `ui/app.css` - steady-state CSS block (~40 lines): body.steady-state inset ring, .ss-badge
  component, keyframes ss-pulse amber exit, reduced-motion + print media queries
- `ui/core.js` - steady-state IIFE (~75 lines): 30s poll of /api/fleet/mode, MutationObserver
  on body[data-fleet-mode], badge inject/remove, CustomEvent dispatch

## Verification
- `python ui/steady-state-verify.py` = **12/12 PASS**
- CSS braces: 391/391 balanced
- JS braces: 397/397, parens: 1377/1377 balanced

## Design Criteria Met
| Criterion | How |
|-----------|-----|
| Green border on cockpit | inset box-shadow rgba(76,175,80,.5) on main when body.steady-state |
| "Converged" badge in header | .ss-badge span injected into modeBar, position:fixed (zero CLS) |
| Reduced animation (calm) | sparkline-deco + panel-enter hidden while steady-state |
| Amber pulse on exit | ss-pulse keyframe 1.2s one-shot via body.ss-exiting class |
| Mode change < 1s | MutationObserver fires same-frame; poll fallback 30s |
| No layout shift | Inset box-shadow + fixed-position badge = zero reflow |
