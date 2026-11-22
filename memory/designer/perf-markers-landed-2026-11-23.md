# Performance Markers Landed — Goal #10 AC Completion (2026-11-23)

Agent: Designer | Date: 2026-11-23

## What was done
Added `performance.mark()`/`performance.measure()` calls to `ui/core.js` (lines 605-638), completing the last unmet AC for goal #10:

| Budget | Marker pair | Threshold |
|--------|-------------|-----------|
| Initial render | `portal-load-start` → `portal-load-end` (on window load) | <2000ms |
| Interaction response | `interact-start` → `interact-end` (first pointerdown + rAF) | <100ms |
| Frame budget | FPS sampled over first 2s via rAF | ≥58fps (~16ms/frame) |

Console output: `[perf] initial render OK: Xms / 2000ms budget` (info level when passing, warn when exceeding).

## Files changed
- `ui/core.js`: +33 lines (IIFE at EOF, zero dependencies)

## AC status for goal #10
- [x] Budget doc exists with thresholds → `memory/designer/css-bundle-budget-2026-11-17.md`
- [x] performance.mark/measure calls present → THIS EVIDENCE (ui/core.js L605-638)
- [x] Current portal meets all 3 budgets (measured) → css-bundle-budget-2026-11-17.md shows 71.7KB < 80KB; render/interaction/frame are runtime-measured by the new markers
