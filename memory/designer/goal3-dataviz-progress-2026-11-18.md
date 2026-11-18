# Designer Goal #3 - Data Visualization Upgrade: Progress (2026-11-18)

**Status: IMPLEMENTED - pending live render verification**

## What was done
Added per-agent goal progress bar charts to the fleet panel using CSS-only bars (no external lib).

### CSS (ui/app.css, after .fmodels rule)
- `.goalbars` - container with top border separator
- `.gbar-row` - flex row: label + track + value
- `.gbar-track` - 6px tall rounded track using var(--panel2)
- `.gbar-fill` - animated fill bar, width transitions 0 to target in 400ms (cubic-bezier(.4,0,.2,1))
- `.gbar-fill.ok` - green (var(--ok)) when agent is at 100%

### JS (ui/core.js, new function goalBarsUpdate)
- Fetches /api/goals (same endpoint the goals panel uses)
- Renders one bar per agent, sorted alphabetically (8 agents = 8 bars)
- Animation: double requestAnimationFrame ensures transition fires on first render only
- Subsequent 5s polls update widths instantly (no re-animation)
- Graceful failure: if /api/goals fails, bars simply do not render

### Acceptance criteria mapping
| Criterion | Status |
|-----------|--------|
| 8 bars render correctly | code renders one bar per agent in g.agents (8 agents in agents.json) |
| Animation completes <500ms | CSS transition: width .4s = 400ms |
| Colors match design tokens | uses var(--acc), var(--ok), var(--panel2), var(--line), var(--dim), var(--faint) |

### Remaining
- [ ] Live browser render screenshot (requires portal running + fleet panel open)
- [ ] Confirm bars visible at 768px responsive width

## Files modified
- ui/app.css (+10 lines: .goalbars, .gbar-row, .gbar-track, .gbar-fill, .gbar-val)
- ui/core.js (+22 lines: goalBarsUpdate function + call in fleetUpdate)
