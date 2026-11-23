# Evidence: Cycle-12 Goal 6 — Autonomy Confidence Decay Indicator
Date: 2026-11-23
Lane: Designer

## Artifacts
- ui/cockpit-decay.css (5972 bytes) — full CSS with 4 decay stages, tokens, light theme, reduced-motion, print
- ui/cockpit-decay.js (3063 bytes) — compute + apply logic, reverify API, periodic tick

## Acceptance Criteria Verification

| Criterion | Status | Proof |
|-----------|--------|-------|
| Decay visible after 24h no re-verification | PASS | `computeStep()` returns step 1 at ageHours >= rateHours (default 24). CSS step 1 desaturates ring to hsl(152,30%,45%) at 75% opacity — visibly distinct from step 0's full green. |
| Re-verified goal snaps back to full confidence | PASS | `reverify(el)` sets data-decay-step="0" + fresh timestamp. CSS `.decay-card[data-decay-step="0"]::before` has `transition: none` — instant snap, no animation. |
| Decay rate configurable via data attribute | PASS | `getRateHours()` reads `data-decay-rate` from the element. Default 24h; any numeric value accepted. JS unit: step = floor(ageHours / rateHours). |
| Does not conflict with state-coherence map (cycle-11 g5) | PASS | Decay ring renders on `::before` pseudo-element positioned at `inset: -4px` — outside the card's own border-box. Card background, border-color, and state-coherence indicators remain untouched. No property collision possible. |

## Design Decisions
- 4 discrete steps (not continuous) to avoid "noise" — operator can read confidence at a glance
- Ring thickness decreases per step (3px → 1.5px) reinforcing the fade semantically
- Step 2+ uses outline (dashed/dotted) instead of box-shadow for textural distinction beyond just color
- `prefers-reduced-motion: reduce` disables all transitions — instant swap
- ARIA: role="status" + aria-label updated per step for screen readers
- Light theme overrides ring colors to maintain contrast on white background

## Integration
- Add `<link rel="stylesheet" href="ui/cockpit-decay.css">` and `<script src="ui/cockpit-decay.js" defer></script>` to index.html
- Any element with class `.decay-card` + `data-verified-at="ISO-timestamp"` auto-initializes
- Call `DecayIndicator.reverify(el)` when a goal is re-verified
