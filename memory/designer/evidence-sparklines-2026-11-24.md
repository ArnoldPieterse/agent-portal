# Evidence: Productivity Sparkline Panel (Goal #5)

Date: 2026-11-24
Status: COMPLETE

## What Was Built
Per-agent mini sparklines (SVG, 7-day window) in ui/cockpit.js showing productive-pass rate.

## Implementation Details
- **Grid layout**: `.ckspark-grid` — CSS grid 4 columns at >=769px; flex horizontal scroll row at <=768px with scroll-snap
- **Per-agent card**: agent name (truncated), SVG polyline sparkline (7 points, viewBox 0 0 100 100), rate percentage
- **Color thresholds**: green >70%, amber 30-70%, red <30% — uses design tokens (--ok, --warn, --err)
- **Tooltip on hover**: `.ckspark-tip` shows "X/Y productive passes" — opacity transition 150ms (well within 200ms requirement)
- **Data source**: reads `productivity_rate`, `total_passes`, `productive_passes`, `productivity_trend` from agent objects in /api/fleet/cockpit response
- **Refresh**: updates on the existing 30s refresh cycle (same as other panels)

## Verification Criteria Met
- [x] 8 sparklines render at 1440px without overflow (4-col grid, min-width:120px per card)
- [x] At 768px they collapse to a horizontal scroll row (media query switches to flex+overflow-x:auto)
- [x] Tooltip appears within 200ms of hover (opacity transition .15s ease = 150ms)
- [x] Data updates on 30s refresh (renderSparklines called in render() which is triggered by the 30s timer)

## Design Decisions
- SVG viewBox with preserveAspectRatio=none: responsive width without JS resize listeners
- Fallback to flat line when no trend data: graceful degradation, still shows current rate color
- scroll-snap-type:x mandatory on mobile: natural card-by-card scrolling

## Artifact
- ui/cockpit.js (modified, 18,220 bytes)
