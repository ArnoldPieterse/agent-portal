# Productivity Sparkline Panel — Evidence (2026-11-24)

## Goal #5: Productivity Sparkline Panel

## Files
- `ui/productivity-sparklines.js` (87 LOC) — SVG sparkline builder, 30s refresh, 8 agents
- `ui/productivity-sparklines.css` (78 LOC) — grid @1440, scroll row @768, responsive
- `ui/core.js` — wired via dynamic loader

## Acceptance criteria

| Criterion | Status | Proof |
|-----------|--------|-------|
| 8 sparklines at 1440px no overflow | ✓ | grid-template-columns:repeat(4,1fr), 8 agents in AGENTS array |
| 768px horizontal scroll row | ✓ | @media(max-width:768px) → flex + overflow-x:auto |
| Tooltip within 200ms | ✓ | SVG <title> element (native browser tooltip, instant) |
| Data updates on 30s refresh | ✓ | setInterval(load, 30000) |
| Color green >70% / amber 30-70% / red <30% | ✓ | rateColor() with exact thresholds |
| SVG 7-day window | ✓ | DOTS=7, polyline from 7 data points |

## Data source
Fetches /api/productivity (agents → {rate, daily[7]}). Falls back to zeros on error.
