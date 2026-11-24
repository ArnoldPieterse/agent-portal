# Mode Transition Animation — Evidence (cycle-15 goal #3)
Date: 2026-11-24
Files: ui/fleet-mode-transition.js (118 LOC), ui/fleet-mode-transition.css (56 LOC)

## Acceptance Criteria Verification (15/15 PASS)
| Criterion | Status | Evidence |
|-----------|--------|----------|
| Background 400ms ease-in-out | PASS | CSS: transition: background 400ms ease-in-out on main::before |
| Green tint (WORK) | PASS | rgba(46,163,107,.06) |
| Amber tint (MAINTENANCE) | PASS | rgba(255,193,7,.08) |
| Grey tint (IDLE) | PASS | rgba(158,158,158,.06) |
| FLIP First phase | PASS | Batched getBoundingClientRect into Map |
| FLIP Last phase | PASS | Second batched read after reorder |
| FLIP Invert phase | PASS | translate(dx,dy) inverse transform |
| FLIP Play phase | PASS | requestAnimationFrame removes transform; CSS transition animates |
| <5 gBCR in Play | PASS | 0 calls in rAF callback (pure CSS animation) |
| prefers-reduced-motion CSS | PASS | @media block disables all transitions |
| prefers-reduced-motion JS | PASS | matchMedia check returns early with instant applyOrder |
| will-change: transform | PASS | GPU compositing hint on .fmt-flip |
| IIFE self-contained | PASS | No global pollution except window.fleetModeTransition API |
| Public API | PASS | {setMode, reorder, transition, ORDERS} |
| Mode-specific orders | PASS | WORK/MAINTENANCE/IDLE arrays defined |

## Integration
- Loaded dynamically via core.js module loader (no index.html edit needed)
- fleet-mode-aria.js calls window.fleetModeTransition.transition(mode, ORDERS[mode]) on detected mode change
- data-fleet-mode set on body for CSS background tint

## Artifact
memory/designer/fleet-mode-transition-verify.json (machine-readable check results)
