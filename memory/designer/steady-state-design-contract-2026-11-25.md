# Steady-State Design Contract (for Verifier transition test)
Date: 2026-11-25
Author: Designer
Purpose: Exact DOM/CSS state reference for verifying steady-state mode transitions.

## State Matrix

| Condition | `body` classes | `.ss-badge` in DOM? | `main` box-shadow | Animations |
|-----------|---------------|--------------------|--------------------|------------|
| WORK (default) | (none) | No | none | Full speed |
| STEADY-STATE | `steady-state` | Yes (in #status) | `inset 0 0 0 2px rgba(76,175,80,.5)` | Paused/suppressed |
| Exit transition (≤2.1s) | `ss-exiting` (then removed) | No (removed before pulse) | amber keyframe animation | One-shot pulse 1.2s |

## CSS Rules (ui/app.css lines ~419-458)
```css
body.steady-state main {
  box-shadow: inset 0 0 0 2px rgba(76,175,80,.5);
}
body.steady-state .sparkline-deco,
body.steady-state .panel-enter { display:none; }
.ss-badge { /* inline-flex pill, green tint */ }
@keyframes ss-pulse { /* amber inset shadow, 3 stops */ }
body.ss-exiting main { animation: ss-pulse 1.2s ease-in-out 1; }
```

## JS Behavior (ui/core.js lines ~642-735)
- **Poll**: GET `/api/fleet/mode` every 30s
- **Entry to STEADY-STATE**:
  1. `document.body.classList.add('steady-state')`
  2. Inject `.ss-badge` element into `#status` container
  3. Dispatch `CustomEvent('steady-state-change', {detail:{mode:'STEADY-STATE'}})`
- **Exit from STEADY-STATE**:
  1. Remove `.ss-badge` from DOM
  2. `body.classList.remove('steady-state')`
  3. `body.classList.add('ss-exiting')` → amber pulse plays (1.2s)
  4. After 2.1s timeout: `body.classList.remove('ss-exiting')`
  5. Dispatch `CustomEvent('steady-state-change', {detail:{mode:'WORK'}})`
- **Test hook**: `window.__steadyStateIndicator.{active, isSteady(), force(mode)}`

## API Contract (`/api/fleet/mode`)
```json
{"mode": "STEADY-STATE|WORK|MAINTENANCE", "since": "ISO8601", "goal_pct": 0.85}
```
Source: `memory/ops/fleet-mode.json` → served by `agent_portal.py` → `fleet_mode_api.handle_fleet_mode()`

## Verification Checklist for Verifier
1. **Entry**: Set mode=STEADY-STATE in fleet-mode.json → within 1s (or next poll): body has class `steady-state`, `.ss-badge` visible, main has green inset shadow.
2. **Exit**: Change mode back to WORK → `.ss-badge` removed, `steady-state` class gone, `ss-exiting` class present for ~2.1s then removed.
3. **No layout shift**: Compare bounding rect of `main` before/after — should be identical (box-shadow doesn't affect layout).
4. **Idempotency**: Call `force('STEADY-STATE')` twice — no duplicate badges, no errors.
5. **Reduced animation**: In steady-state, `.sparkline-deco` and `.panel-enter` elements have `display:none`.

## Files to Inspect
- `ui/app.css` lines 419-458 (CSS)
- `ui/core.js` lines 642-735 (JS IIFE)
- `memory/ops/fleet-mode.json` (data source)
- `agent_portal.py` (API route)