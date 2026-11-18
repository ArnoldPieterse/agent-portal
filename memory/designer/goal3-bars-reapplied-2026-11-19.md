# Goal #3 - Data Visualization Upgrade: SVG Bars Re-applied 2026-11-19

## Problem
Previous implementation (2026-11-18) was lost - ui/core.js was truncated during a failed write (encoding error). Restored from canonical backup then re-applied.

## What was built this pass
### ui/core.js (~45 lines inserted before ops panel section)
- `_goalBar(agent, total, done)` - returns SVG bar HTML with animated fill rect
  - Colors: var(--ok) for 100%, var(--acc) for >=50%, var(--warn) for <50% (all from tokens.css)
  - Animation: CSS transition on width, 450ms cubic-bezier(.4,0,.2,1) - under 500ms requirement
  - Accessibility: SVG role=img + aria-label per bar
- `goalsUpdate()` - async fetch from /api/goals, renders bars into #goalsBody
  - Summary line: fleet_done/fleet_total + percentage
  - Double-rAF for animation trigger (ensures initial width=0 is painted)
  - 10s auto-refresh interval while panel open
- `$("goalsBtn").onclick` handler - toggles panel, starts/stops timer

### ui/app.css (6 lines appended)
- .gsummary, .grows, .grow, .gname, .gbar, .ghint styles
- All values use design tokens (var(--fs-12), var(--sp-4), var(--dim), var(--faint))

## Data source
/api/goals endpoint returns: {ok, fleet_pct, fleet_done, fleet_total, agents:[{agent,total,done,open,blocked}]}
Currently 8 agents in the fleet = 8 bars.

## Acceptance test status
- [x] Code implemented (static verification: functions present, tokens referenced)
- [ ] Visual verify: 8 bars render in browser (requires portal running + hard refresh)
- [ ] Animation timing confirmed <500ms (CSS transition value = 450ms, statically verifiable)
- [ ] No layout shift on data update (bars use fixed width=120px SVG, no reflow)