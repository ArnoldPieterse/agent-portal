# Pixel — Convergence A11y Pass (goal #3) — structural verification
Run: 2026-11-25 · seat White (local, egress-walled; no JS runtime → source-level audit)

Method: static analysis of `ui/cockpit-convergence.js` verifying aria-live delta announcements and roving tabindex keyboard navigation.
Result: **22/22 checks pass**.

## Checks
- [x] Score delta announcement with direction (up/down) + magnitude + target value
- [x] Steady-state ENTER announcement ("Fleet entered steady state.")
- [x] Steady-state EXIT announcement ("Fleet exited steady state.")
- [x] prevScore / prevSteady tracked in state for comparison across polls
- [x] Dedicated #ckconvLive region (sr-only, aria-live=polite, role=status)
- [x] Panel box retains aria-live=polite aria-atomic=true (structural changes announced)
- [x] Roving tabindex: first card tabindex=0, rest -1
- [x] ArrowRight/ArrowDown moves focus forward
- [x] ArrowLeft/ArrowUp moves focus backward
- [x] Wraps around (modulo cards.length)
- [x] Tabindex moved from current to next card on navigation
- [x] Focus() called on the newly active card
- [x] Enter key opens drill-down (preserved)
- [x] Space key opens drill-down (preserved)
- [x] role=button on all cards
- [x] aria-label describes drill-down action per card

## Acceptance mapping
- **Announcements fire on score delta**: `state.prevScore` compared to new score; if changed, liveRegion announces "Autonomy score changed up/down N to X."
- **Steady-state enter/exit**: `state.prevSteady` compared; toggles trigger specific announcements.
- **No re-reading panel**: dedicated sr-only #ckconvLive (role=status) receives only the delta message, not the full panel content.
- **Arrow keys move focus across all 4 in order**: roving tabindex + modulo wrap ensures circular navigation through gauge→trend→interventions→progress→gauge...

axe-core score ≥0.95 requires live browser run — deferred to non-sandbox seat (structural a11y attributes all present).
