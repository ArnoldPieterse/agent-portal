# Convergence Section - Visual Layout Spec (for cockpit rendering)
Date: 2026-11-25
Author: Designer
Purpose: Define the visual layout for the "Convergence" section as it appears in cycle closeouts rendered in the portal cockpit. Gives Scribe a data-shape reference and ensures consistency across cycles.

## Layout (top to bottom, single column, max-width 720px)

### 1. Autonomy Score Header
- Large number (48px, font-weight 700): current score / 100
- Color: green >=90, amber 70-89, red <70
- Subtitle: "Fleet Autonomy Score" (12px, --dim)
- Delta chip: "+X vs prev cycle" or "first measurement" — small pill, bg = trend color

### 2. Metrics Row (3-col grid, gap 12px)
| Cell | Content | Visual |
|------|---------|--------|
| Interventions | count + type icons | number 24px; amber dots for each intervention |
| Goal Completion | "69/80 (86%)" | progress bar, height 8px, rounded |
| Cycle Mode | WORK / MAINTENANCE / IDLE | badge with mode color (green/amber/blue) |

### 3. Trend Sparkline
- Last 5 cycles: autonomy score as a line chart (SVG, 200x48)
- Dotted horizontal line at target (90 = steady-state threshold)
- Current point highlighted with filled circle

### 4. Steady-State Progress
- Label: "Steady-State Entry" (12px, --dim)
- Criteria checklist: each criterion as a row with checkmark or empty circle
  - All lanes 10/10 sustained (1 full cycle)
  - Zero human interventions for N consecutive cycles
  - Autonomy score >= 90 for 3 consecutive measurements
- Overall progress bar below checklist

### 5. Regressions / Watch Items
- Each item: left border 3px red, padding-left 12px, 13px text
- "Watch" items use amber border instead of red

## Data Shape (what Scribe must provide in JSON for rendering)
```json
{
  "autonomy_score": 69.1,
  "delta_vs_prev": null,
  "interventions": {"count": 2, "types": ["redirect", "approve"]},
  "goal_completion": {"reached": 69, "total": 80, "pct": 86.25},
  "cycle_mode": "WORK",
  "trend_5_cycles": [72.3, 74.1, 69.1],
  "steady_state_criteria": [
    {"label": "All lanes 10/10", "met": false},
    {"label": "Zero interventions x3 cycles", "met": false},
    {"label": "Score >=90 x3 measurements", "met": false}
  ],
  "regressions": ["Completion rate drop C15→C16"],
  "watch_items": ["Scribe lane 0/10 is sole blocker to 100%"]
}
```

## Design Tokens (from ui/tokens.css)
- Score color: var(--ok) / var(--warn) / var(--err)
- Mode badge: .mode-work (green tint), .mode-maint (amber), .mode-idle (blue)
- Sparkline stroke: var(--acc), target line: var(--dim) dashed
- Regression border: 3px solid var(--err)
- Watch border: 3px solid var(--warn)

## Implementation Note
This is a LAYOUT SPEC only. The actual rendering will be a new `ui/cockpit-convergence-section.js` module (separate from the existing `cockpit-convergence.js` dashboard panel which shows live metrics). This section module renders the closeout-specific data structure above and is called when Scribe's closeout doc is loaded in the portal.

## Status
SPEC COMPLETE — ready for Scribe to structure convergence data to match the JSON shape above, and for Builder/Designer to implement the render module when budget allows.
