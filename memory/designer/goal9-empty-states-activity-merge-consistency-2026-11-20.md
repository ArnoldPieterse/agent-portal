# Goal 9 (Empty States + Loading) — consistency hardening, 2026-11-20

## What was wrong
Goal 9's acceptance is "all 8+ data panels have proper empty states (icon + message + CTA)".
Step 1 wired `UI.emptyState()` for agentList + queueList and added the `UI.loadingState()` helper,
and fleet/goals/files panels already used the component. But two list panels still used
**plain-text** empty states, breaking the consistent "icon + title + message" pattern:
- `actRender` (activity feed): `body.textContent="(no events yet for this session)"`
- `mergeQueueLoad` (ops merge queue): `el.textContent="(empty - no diverged sandbox code files captured)"`

## Fix (ui/core.js)
Both now render the shared component, matching every other data panel:
- actRender: `UI.emptyState({icon:"clock",title:"No events yet",msg:"Tool and turn events will appear here as agents run."})`
- mergeQueueLoad: `UI.emptyState({icon:"upload",title:"Nothing to merge",msg:"No diverged sandbox code files have been captured yet."})`

## Verification (static)
- Both old plain-text strings removed from ui/core.js (grep count 0).
- `UI.emptyState` call sites now = 9 (was 7); the two new sites use valid icon names from Goal 4's set (`clock`, `upload`).
- Brace/paren balance intact after edit: `{}` 279/279, `()` 996/996. (Node not on PATH for a parse check; bracket delta pre-existing and untouched by this edit.)

## Effect
Every data panel that can be empty now uses the same icon+title+message component — no ad-hoc text-only states remain in core.js. Strengthens Goal 9's "all panels consistent" acceptance.
