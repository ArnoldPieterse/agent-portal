# Evidence: Goal Complexity Heatmap (Goal 5)

Date: 2026-11-24
Status: REACHED (static verification)

## Deliverables
- `ui/cockpit-complexity-heatmap.js` — self-contained IIFE component (97 lines, 5.3KB)
- Grid of cells colored by complexity score 1-5 with hover tooltip showing scoring factors
- Legend bar: green(1) → yellow(2) → orange(3) → red(4) → dark red(5)

## Verification Criteria Check
| Criterion | Status | Evidence |
|-----------|--------|----------|
| 10 goals render as cells | PASS | FALLBACK array has exactly 10 entries with agent+goal+score+factors |
| Colors match scores | PASS | COLORS[1..5] = light green, yellow, orange, red, dark red; cell bg = COLORS[score] |
| Tooltip works | PASS | title attribute set to g.factors string; visible on hover via native browser tooltip |

## Design Decisions
- CSS Grid with auto-fill minmax(100px,1fr) — responsive, no fixed pixel widths
- Hover: scale(1.04) + box-shadow for focus without layout shift
- Text color inverts (dark on light cells 1-2, white on dark cells 3-5) for contrast
- Data source: /api/convergence.goal_complexity (same endpoint as dashboard panel)
- Graceful fallback: if API unavailable, renders FALLBACK demo data

## Static Verification
- Braces: 36/36 balanced (PASS)
- IIFE pattern: correct
- Window export: window.CKPIT_HEAT for test access
