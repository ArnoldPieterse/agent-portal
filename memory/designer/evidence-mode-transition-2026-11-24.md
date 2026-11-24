# Mode Transition Animation — Evidence (2026-11-24)

## Goal #3: Mode Transition Animation

## Files
- `ui/fleet-mode-transition.js` (97 LOC) — FLIP reorder + setMode + public API
- `ui/fleet-mode-transition.css` (56 LOC) — background tint per mode, 400ms ease-in-out
- `ui/core.js` — wired both files via dynamic loader

## Acceptance criteria

| Criterion | Status | Proof |
|-----------|--------|-------|
| Background shift green→amber→grey, 400ms ease-in-out | ✓ | CSS: data-fleet-mode selectors with rgba tints, transition: background 400ms ease-in-out |
| Panel reorder uses FLIP (not instant) | ✓ | JS: First/Last/Invert/Play pattern, transform transitions |
| getBoundingClientRect <5 during Play phase | ✓ | 0 calls in rAF callback (CSS animates) |
| Reduced-motion respected | ✓ | CSS @media(prefers-reduced-motion:reduce) + JS matchMedia check |
| No layout thrashing | ✓ | Batched reads (FIRST, LAST phases), writes isolated from reads |

## Integration note
Works with cockpit-mode-layout.js (g1): transition module handles visual reorder animation,
layout module handles content changes (goal collapse, IDLE hero). No conflicts.
