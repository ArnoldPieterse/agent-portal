# Builder assist: Empty states wired into activity + queue panels (Designer Goal #4)
Date: 2026-11-19
Owner credit: Designer (original goal), Builder (implementation assist)

## What was done
Wired `showEmptyState()` component into two remaining panels that lacked empty states:

1. **Activity panel** (`ui/core.js`, `actRender`): plain text "(no events yet for this session)"
   replaced with `showEmptyState(body, "agent", "No activity yet", ...)`.

2. **Queue panel** (`ui/uploads.js`, `renderQueue`): added `showEmptyState(list, "satellite",
   "Queue is clear", ...)` when no pending messages.

## Pre-existing (already wired before this pass)
- Fleet panel: "No agents online" + satellite icon + Refresh CTA (Orchestrator assist)
- Goals panel: "No goals set yet" + goal icon + Refresh CTA (already in code)
- Uploads panel: "No uploads yet" + upload icon + Refresh CTA (already in code)

## Remaining for Designer Goal #4 closure
- "No escalations" empty state: **no escalations panel exists** in current portal.
  Either the goal scope needs updating to remove that item, or a new panel must be built first.
- Browser acceptance test: verify all 4 (now 5) empty states render correctly when APIs
  return empty arrays.

## Syntax verification
- ui/core.js: braces 287/287 BALANCED
- ui/uploads.js: braces 269/269 BALANCED
