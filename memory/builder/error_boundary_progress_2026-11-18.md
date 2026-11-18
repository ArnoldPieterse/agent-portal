# Error Boundary + Fallback UI — Progress (2026-11-18)

## What was done
1. **CSS** (`ui/app.css`): Added `.panel-error` card styles (icon, message, retry button). Works in both dark and light themes via CSS variables.

2. **JS helper** (`ui/core.js`): Added `showPanelError(el, msg, retryFn)` and `safePanel(el, fn)`:
   - `showPanelError`: replaces element content with styled "panel unavailable" card + retry button
   - `safePanel`: async wrapper — calls fn(), on error invokes showPanelError with self-retry

3. **Panel integration** (3 main panels upgraded):
   - Activity panel: catch block now shows error card in `#actBody` with retry → re-calls actUpdate
   - Fleet panel: catch block shows error card in `#fleetBody` with retry → re-calls fleetUpdate
   - Ops panel: catch block shows error card in `#opsBody` with retry → re-calls opsLoad

## Verification
- Bracket/paren balance confirmed (code-level, string-stripped)
- Helper defined before first use (char positions verified)
- CSS uses existing design tokens (--dim, --line, --acc, --sel-bg) so both themes work
- Retry button clears error card and re-invokes the panel update function

## Remaining for full closure
- Browser render test: kill API → verify fallback cards appear → restart API → click retry → panels restore
- Sub-panels (mergeQueue, perfLoad, eventsLoad) could also get individual boundaries but they're nested within opsBody which already has one
- Acceptance criterion "killing the API mid-session shows fallback cards" requires live test

## Files modified
- ui/app.css (+5 lines: .panel-error styles)
- ui/core.js (+16 lines: helper functions, 3 catch-block upgrades)
