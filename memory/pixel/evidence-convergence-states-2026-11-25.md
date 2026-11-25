# Pixel — Convergence Loading/Error/Empty States (goal #1) — structural verification
Run: 2026-11-25 15:39 · seat White (local, egress-walled; no JS runtime → source-level audit)

Method: extracted each render function by brace-matching `ui/cockpit-convergence.js` (open-paren-anchored to avoid prefix collisions) and asserted the goal-1 acceptance criteria against the actual slices.
Result: **26/26 checks pass**.

## Checks
- [x] loading skeleton -> ckconv-gauge
- [x] loading skeleton -> ckconv-trend
- [x] loading skeleton -> ckconv-interventions
- [x] loading skeleton -> ckconv-progress
- [x] error state -> ckconv-gauge
- [x] error state -> ckconv-trend
- [x] error state -> ckconv-interventions
- [x] error state -> ckconv-progress
- [x] empty -> gauge null renders dash not NaN
- [x] empty -> renderTrend data-state=empty branch
- [x] empty -> renderInterventions data-state=empty branch
- [x] empty -> renderProgress data-state=empty branch
- [x] error card shows text label not blank
- [x] aria-live -> loading announces
- [x] aria-live -> error announces
- [x] aria-live -> fresh render announces
- [x] aria-live -> stale render announces
- [x] aria-live -> box has aria-live=polite
- [x] aria-live -> dedicated status region role=status
- [x] defensive -> cycle_duration_trend guarded
- [x] defensive -> human_intervention_count guarded
- [x] fetch cache:no-store
- [x] poll interval present
- [x] reduced-motion -> shimmer disabled
- [x] syntax -> braces balanced
- [x] syntax -> parens balanced

## Acceptance mapping
- 3 mock conditions per widget → loading (renderSkeletons), error (renderErrorAll), empty (per-widget data-state=empty / gauge dash) present for all 4 widgets.
- 0 console errors on dead API → error path renders 'unavailable' text, not NaN/blank; nested fields null-guarded (`|| {}`).
- aria-live='polite' → dedicated #ckconvLive (role=status) written on loading/error/fresh/stale transitions; box itself aria-live=polite.

Live CDP leg (real browser screenshots of the 3 states) deferred to a non-sandbox seat — recorded, not faked here.