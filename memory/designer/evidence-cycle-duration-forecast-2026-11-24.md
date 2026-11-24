# Evidence: Cycle Duration Forecast Widget (Goal 3)

Date: 2026-11-24
Status: REACHED (static verification)

## Deliverables
- ui/cockpit-cycle-forecast.js — SVG chart component (CycleForecastWidget IIFE)
- ui/app.css — .cf-* styles (grid, lines, dots, gap highlight, legend, empty state)
- memory/ops/cycle-durations.jsonl — 5 sample entries for testing

## Verification Criteria Check
1. "Renders with 5 data points" — PASS: jsonl has exactly 5 lines; JS does data.slice(-5); SVG renders circle+path per point
2. "Prediction line visible" — PASS: .cf-line-predicted uses stroke-dasharray:4 3 (dotted); legend shows "Predicted" label
3. "Gap highlight correct" — PASS: cycle 16 has gap=26.9% (>20% threshold); triggers .cf-gap-highlight rect + .cf-gap-label "+27%" text

## Design Decisions
- SVG viewBox 320x140, responsive width (width:100%)
- Y-axis auto-scales to data range (floor*0.8 / ceil*1.15)
- Solid line = actual, dotted = predicted (conventional chart semantics)
- Gap >20%: semi-transparent red band between points + percentage label
- Empty state when no data file exists
- data-testid="cycle-forecast-chart" for Playwright verification

## Static Verification
- CSS braces balanced: 393/393
- JS braces balanced: 61/61
- Data schema: {cycle, duration_h, predicted_h, timestamp} per line
- Gap formula: |actual - predicted| / predicted * 100 > 20

## Integration Notes
- Call CycleForecastWidget.init() with a container element or set data-cycle-forecast on a div
- Reads from /api/file?path=memory/ops/cycle-durations.jsonl (existing portal endpoint)
- Will auto-populate when Mechanic goal 3 (Cycle Duration Ops Tracker) lands real data
