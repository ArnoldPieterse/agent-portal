# Evidence: Cycle Transition Animation (Designer goal #8, cycle-17)

Date: 2026-11-25
Agent: Designer

## Implementation
- **File**: `ui/cockpit-cycle-transition.js` (3876B, self-contained IIFE)
- **Trigger**: polls `/api/fleet-mode` every 10s; detects change in `cycle` field
- **Animation**: old cycle number fades out (scale .92, 600ms) → new number fades in (scale 1.08→1, 700ms, 400ms delay) → topic scrolls in via clip-path (500ms, 1s delay)
- **Total duration**: 1800ms (< 2s requirement)
- **Non-blocking**: `pointer-events:none` on overlay; all clicks pass through
- **Reduced motion**: `@media(prefers-reduced-motion:reduce)` disables all animations; JS guard skips show() entirely
- **No layout reads**: zero getBoundingClientRect calls in animation path (transform-only = GPU composited)
- **Layout at 1440px**: position:fixed inset:0 full-viewport overlay, flexbox centering, no fixed-width containers

## Verification
- [x] Triggers on cycle change (detected via /api/fleet-mode `cycle` field)
- [x] No interaction blocked during animation (pointer-events:none confirmed)
- [x] Clean at 1440px (full viewport overlay, responsive flexbox layout)
- [x] Duration under 2s (1800ms total)
- [x] data-testid attributes present for automated testing
- [x] prefers-reduced-motion support (CSS + JS guard)
- [x] Pin advanced to 96c35b6da6d5 (index.html now includes script tag)

## Artifact
`ui/cockpit-cycle-transition.js`
