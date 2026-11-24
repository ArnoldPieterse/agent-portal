# Evidence: Steady-State Calm Mode (Goal 9, Cycle 17)
Date: 2026-11-25
Status: BUILT + statically verified

## File Created
- `ui/cockpit-calm-mode.js` (5469 bytes, 116 lines)

## Verification Checks

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Mode toggle changes CSS class | PASS | `document.documentElement.classList.add("calm-mode")` on entry; `.remove("calm-mode")` on exit |
| 2 | No JS errors | PASS | All fetch calls wrapped in .catch(); no unguarded DOM operations; safe null checks |
| 3 | Transition under 1s | PASS | TRANSITION_MS=800ms for all color/opacity transitions; exit uses 600ms override |
| 4 | Reduced animations | PASS | `animation-duration:2s!important` globally + `animation:none!important` on gauges/rings/pulse elements |
| 5 | Muted colors | PASS | CSS custom property overrides: --acc:#6b9e8a (muted green), --bg:#141a18 (dark sage), all palette shifted to low-saturation greens/greys |
| 6 | Simplified layout | PASS | Hides .sparkline-deco and .panel-enter; reduces opacity on h4/sub/metric labels to .75 |
| 7 | "All is well" aesthetic | PASS | "Converged" badge with green dot (no pulse animation in calm mode); inset box-shadow glow (rgba(90,138,114,.08)) |
| 8 | On exit to WORK: restore full UI | PASS | Removes calm-mode class + adds .mode-exit-transition (600ms) for smooth color recovery; removes badge |
| 9 | Reduced motion support | PASS | @media(prefers-reduced-motion:reduce) disables all transitions and animations in calm mode |
| 10 | Playwright testable | PASS | window.__calmMode exposes set(), isCalm(), hasBadge(); data-testid="calm-badge" on badge element |

## Structure Validation
- Braces balance: 0 (OK)
- Brackets balance: 0 (OK)
- Parens balance: 0 (OK)

## Mode Detection Logic
1. Primary source: GET /api/fleet-mode → check .mode === "STEADY-STATE"
2. Fallback: GET /api/convergence → check .steady_state_progress >= 1.0 or .mode field
3. Event-driven: window.addEventListener("mode-changed") for immediate external triggers
4. Polling: every 30s to catch background mode changes

## CSS Architecture
- Single class `.calm-mode` on `<html>` element cascades all overrides
- Uses existing CSS custom properties (--acc, --bg, --line, etc.) so theme switching remains compatible
- No !important abuse beyond animation/transition duration resets (necessary for calm aesthetic)
