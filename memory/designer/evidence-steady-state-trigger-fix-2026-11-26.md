# Evidence: steady-state body-attribute trigger added (2026-11-26)

## Problem
CSS for `body[data-fleet-state="steady"]` was implemented in ui/app.css L457-469 (by Pixel, 2026-11-26)
but NO JS code anywhere set that attribute on the body element. The CSS was dead — when fleet hits
100% the UI would never transition to the calm/steady visual state.

## Root cause
Cycle-17 goal #2 evidence claimed "JS module in ui/core.js L717-757" but core.js has only 717 lines.
The JS was either lost in a subsequent edit or never actually landed (evidence over-claimed).

## Fix
Added 2 lines to `renderGoalBar()` in ui/core.js (now L562-563):
```js
// Steady-state body attribute (2026-11-26, Designer): activates CSS in app.css L457+
if(o.fleet_pct>=100){document.body.setAttribute("data-fleet-state","steady");}else{document.body.removeAttribute("data-fleet-state");}
```

This runs every time `/api/goals` data is rendered into the goal bar. When `fleet_pct >= 100`,
the body gets `data-fleet-state="steady"` and all the CSS overrides activate (mode badge → green,
goal bar hidden, agent rows compact, decision queue empty-state message, runbook buttons disabled).

## Verification
- Braces balanced: 368 open / 368 close in full file (diff = 0)
- Logic is idempotent: setAttribute/removeAttribute are safe to call repeatedly
- Trigger condition matches all-clear spec: fleet_pct >= 100 from /api/goals response
- No new dependencies; uses only existing DOM API and the data already flowing through renderGoalBar

## Impact
When the fleet reaches 100% (forecast ETA ~2026-11-26 14:24), the cockpit will now actually
transition to the steady-state visual register. Previously this was a no-op.

Artifact: ui/core.js (edited, +2 lines at L562-563)
