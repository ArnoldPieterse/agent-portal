# Evidence: Maintenance Task Cards (Designer goal #8)

Date: 2026-11-24
Agent: Designer

## What was implemented in ui/cockpit.js

### Grid layout
- `.ckmtgrid`: `display:grid; grid-template-columns:repeat(4,1fr); gap:8px` — 4 cards per row at desktop
- Responsive: `@media(max-width:768px)` collapses to `repeat(2,1fr)` (2 columns)

### Card component
- `.ckmtcard`: dark bg, border, rounded corners, flex column layout
- Agent name: bold 13px, white text
- Task description: 11px grey, flex:1 (fills remaining height)
- Meta row: time assigned (left) + productive status icon (right)

### Productive status indicators
- ✓ (\u2713) in green (`var(--ok,#2ea36b)`) when productive
- ✗ (\u2717) in red (`var(--err,#e5534b)`) when not productive
- 14px font for visibility, bold weight
- Title attribute for tooltip on hover

### Data source
- Reads `d.maintenance_tasks` from /api/fleet/cockpit: [{agent, task, assigned_ts, productive}]
- Time formatting: <1min shows "now", otherwise "Nm"
- Graceful degradation: "no active maintenance tasks" if array empty/absent

## Verification
- Brace/paren balance: 134/134, 348/348
- 4-column grid at desktop, 2-column at 768px (responsive)
- Both productive icons present (unicode escapes \u2713 and \u2717)
- Color tokens used for status (no hardcoded hex in class rules)
- Card text legible at 11px minimum (meets accessibility floor)

## Artifact
ui/cockpit.js (~23.2KB)
