# Builder Goal 6 — State Management Refactor (Increment 1)
Date: 2026-11-20

## What was done
1. Created `ui/state.js` (36 lines) — plain script exposing `window.State` with:
   - `getState(key?)` — read one key or full snapshot
   - `setState(key, value, opts?)` — write + notify subscribers
   - `subscribe(key, fn)` — returns unsubscribe function
   - `seedState(obj)` — bulk-initialise at boot
2. Added `<script src="ui/state.js"></script>` before core.js in index.html.
3. Wired `selectedId` (7 occurrences) through State:
   - Declaration replaced with State.seedState call
   - All 5 read sites changed to State.getState('selectedId')
   - 1 write site changed to State.setState('selectedId', a.id)
   - 0 bare selectedId refs remain in core.js

## Verification (in-process)
- Brace balance: 305/305 PASS
- Paren balance: 1114/1114 PASS
- grep for bare selectedId outside State calls: 0 hits PASS

## Remaining for full closure
- Wire mode (18 occ) and busy (6 occ) through State
- Wire data collections (agents, models, etc.) when they stabilise
- Add subscribe-based re-render triggers
- 10-min soak test with no stale-state bugs

## Files changed
- ui/state.js (new, sha12=8f6f8f23e321)
- ui/core.js (6 lines modified)
- index.html (1 script tag added — pin advance needed)
