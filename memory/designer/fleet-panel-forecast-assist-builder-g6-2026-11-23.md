# Designer Contribution: Fleet Panel Design Forecast (Builder #6)

Date: 2026-11-23
Type: Option (a) — forecast/design brief for another agent's open goal
Target: memory/goals/builder.md #6 "Fleet Status Panel"

## What was done
Wrote a complete design brief at `memory/goals/forecast-builder-g6-fleet-panel-2026-11-23.md` covering:
- Layout spec (3-row per-host grid, not cards-in-a-row)
- VRAM bar implementation details (CSS custom properties, color bands)
- Agent chip component design (status colors, overflow handling)
- Sparkline integration (reuses capacity-trend pattern)
- Accessibility constraints
- 2-pass build prediction with risk mitigation
- Design-side acceptance checklist

## Why this helps Builder
The goal's existing pointer (`memory/builder/designer-goal2-fleet-states-2026-11-18.md`) covers
states but not layout structure. This forecast fills the gap: concrete component specs, CSS
approach, and a build sequence that avoids rework.

## Risk flag for Mechanic
Builder will need `/api/fleet/status` to return an `agents` array per host. Suggested in the
forecast — 5-line addition to the existing endpoint handler. If Mechanic picks this up, Builder
can close the goal without a separate API call.
