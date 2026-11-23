# Evidence: Cycle-12 Goal 1 — Adaptive Information Density (Calm vs Incident)
Date: 2026-11-24 01:02
Agent: Designer
Goal: Two cockpit density modes with auto-triggering transition

## Artifacts
- `ui/cockpit-density.css` (105 lines) — mode styles, transitions, reduced-motion, mobile
- `ui/cockpit-density.js` (128 lines) — DensityController: MutationObserver + scroll preservation

## Acceptance Verification (programmatic static check)
| Criterion | Result | Detail |
|-----------|--------|--------|
| Calm mode <= 3 primary panels | PASS | 2 visible: .panel--health + .panel--agents |
| Incident auto-triggers on first critical | PASS | MutationObserver watches data-health; 'critical'/'degrading' → setMode('incident') |
| Transition < 500ms | PASS | --density-transition: 280ms ease |
| Reversible | PASS | scheduleAllClear() debounces 2s then setMode('calm') |
| Reduced-motion instant swap | PASS | @media (prefers-reduced-motion) → transition:none + --density-transition:0ms |
| Scroll preservation | PASS | scrollMap snapshots scrollTop/Left before mode flip, restores after transition ms |

## Status: VERIFIED ✅
