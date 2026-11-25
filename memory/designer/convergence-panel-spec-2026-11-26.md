# Design Spec: Convergence Dashboard Panel (Builder Goal #2 assist)
Author: Designer | Date: 2026-11-26 | Status: DRAFT for Pixel/Builder implementation

## Context
Builder goal #2 requires a convergence panel in ui/cockpit.js showing:
- Autonomy score sparkline (last 10 cycles)
- Intervention count bars per cycle
- Efficiency trend line (verified goals / total goals per cycle)

Polls `/api/convergence/trend` every 5 min. Must be <100 lines added to cockpit.js.

## Layout (fits existing 6-panel grid, adds as panel #7 or replaces a slot)
```
+------------------------------------------+
| CONVERGENCE TREND            [refresh]   |
+------------------------------------------+
|                                         |
|  Autonomy:    [sparkline ~80px tall]    |
|              42 -> 58 -> 71 -> 83       |
|                                         |
|  Interventions:                         |
|              [bar chart, 10 bars]        |
|              12  9   7   5   3   2 ...  |
|                                         |
|  Efficiency:                            |
|              [line chart ~60px tall]    |
|              62% -> 71% -> 78% -> 84%   |
+------------------------------------------+
```

## Visual Spec
- **Sparkline** (autonomy): SVG polyline, stroke `var(--accent)`, width 2px. Dots at each data point r=3. Gradient fill below line (opacity 0.1). Color shifts: red<40, yellow 40-70, green>70.
- **Bars** (interventions): CSS flexbox row of divs. Height = count/maxCount * 60px. Color: single hue, opacity 0.8. Tooltip on hover shows cycle number + count.
- **Line** (efficiency): SVG polyline like sparkline but dashed. Y-axis label at start/end showing %.

## Data Contract (from /api/convergence/trend)
```json
{
  "cycles": [
    {"n": 9, "autonomy_score": 42, "interventions": 12, "efficiency_pct": 62},
    ...
  ]
}
```

## Implementation Notes for Pixel
1. Add `renderConvergencePanel(data)` function in cockpit.js IIFE scope.
2. Reuse existing `el()` helper from ui/components.js for DOM construction.
3. SVG inline (no library). Keep total <100 lines.
4. Hook into existing 30s refresh cycle (piggyback on the same setInterval, add fetch to /api/convergence/trend).
5. If endpoint returns 404, show "Convergence data unavailable" placeholder (don't crash panel grid).

## Acceptance Mapping
| AC criterion | How spec satisfies it |
|---|---|
| Renders from live API data | Polls /api/convergence/trend; renders on success |
| 3 mock datasets render correctly | Deterministic SVG/CSS from array input = testable with fixed arrays |
| No console errors | Graceful 404 handling; no undefined refs |
| <100 lines added | SVG + flexbox approach is compact; budget ~85 lines |

## Effort Estimate
~45 min for Pixel (familiar with cockpit.js patterns from cycle-7 work).
