# Goal 9 - Empty States + Loading Patterns: Step 1 (2026-11-20)

## What was done
Added missing empty states and a loading-state helper:

1. **`UI.loadingState(el, minMs)`** in `ui/core.js` — new helper that shows a skeleton
   in the given element and resolves after >=500ms minimum display time (prevents flash).
   Uses the existing `.i-skel--line` class from interactions.css.

2. **`agentList` empty state** in `ui/core.js` `renderAgents()` — when `agents.length === 0`,
   renders `UI.emptyState({icon:"agent", title:"No agents configured", ...})` with a CTA
   button that triggers the Add Agent flow.

3. **`queueList` empty state** in `ui/uploads.js` `renderQueue()` — when no pending rows,
   renders `UI.emptyState({icon:"clock", title:"Queue empty", ...})`.

4. **Skeleton class migration** — `UI.skeleton()` now emits `.i-skel--line` (the interaction
   system class) instead of the old `.skeleton` class, unifying loading patterns under one
   CSS source.

## Files changed
- `ui/core.js`: +2 lines (empty state in renderAgents), +3 lines (UI.loadingState helper), skeleton class rename
- `ui/uploads.js`: 1 line changed (queueList empty state)

## Verification
- Brace/paren balance: both files pass (core.js 277/277, uploads.js 251/251)
- All three panels now use the shared `UI.emptyState()` pattern (icon + title + msg + optional CTA)
- Skeleton uses `.i-skel--line` which has shimmer animation + prefers-reduced-motion fallback

## Remaining for full Goal #9 closure
- opsBody: has static git-status layout, not truly "empty" — low priority
- actBody (chat): always has at least the composer; no data-empty case
- Wire `UI.loadingState()` into >=2 real async fetch sites to demonstrate min-time skeleton
