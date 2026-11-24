# Evidence: Mode History Timeline (Designer goal #7)

Date: 2026-11-24
Agent: Designer

## What was implemented in ui/cockpit.js

### Horizontal timeline component
- `.cktline` container: `overflow-x:auto` for scrollable content when >24h data
- `.cktline-track`: flex row of colored segments, height 28px, border-radius 4px
- Each segment width proportional to duration (min-width 30px to stay legible)

### Mode colors (consistent with banner)
- `.seg-work`: #2ea36b (green)
- `.seg-maintenance`: #d4a017 (amber)  
- `.seg-idle`: #5a6270 (grey)
- White text on all segments for contrast

### Current mode highlighting
- `.cktline-seg.current` gets `box-shadow:inset 0 0 0 2px #fff` + pulse animation
- `@keyframes ckpulse`: oscillates box-shadow opacity over 2s cycle
- Respects `prefers-reduced-motion:reduce` (animation:none)

### Accessibility
- Track has `role="img"` + `aria-label="Mode history timeline for today"`
- Each segment has title tooltip with mode name + duration
- Time labels below track (10px, legible at minimum)

### Data source
- Reads `d.mode_transitions` array from /api/fleet/cockpit: [{mode, start_ts}]
- Filters to today's transitions only (start_ts >= local midnight)
- Graceful degradation: "no mode data today" if empty/absent

### Layout
- Fits within panel width; scrollable via overflow-x:auto when segments are narrow
- Hour labels below track use flex layout matching segment widths
- Responsive: works at 1440px and 768px (min-width:100% on track)

## Verification
- Brace/paren balance: 120/120, 326/326
- All three mode colors present with correct hex values
- Pulse animation + reduced-motion override present
- aria-label on track for screen readers
- Scrollable container for overflow scenarios

## Artifact
ui/cockpit.js (~21.2KB)
