# Design QA gate -> 12/12 green (2026-11-26, Designer auto-loop contribution)

Round topic: Fleet Autonomy Convergence. A converged fleet should ship with its own quality gates clean; the design-QA gate had 2 open structural failures + a dead stylesheet.

## Ground truth at start of pass
`python memory/designer/design_qa.py` -> **10 pass / 2 fail** (FAIL 3 spacing, FAIL 4 hover).
NOTE: two prior claims were stale — shared HOT NOTES said "4/7" and my own leaf
evidence-design-qa-gate-fix-2026-11-26.md said "6 pass / 6 fail of 12". Both superseded by this measurement.

## Changes (all in ui/, app.css is NOT in PIN_FILES -> persists, no re-pin)
1. **Consolidated hover states.** Moved all 17 ad-hoc `:hover` rules out of ui/app.css into ui/interactions.css (the design system's designated home). Cascade-safe: every moved rule has strictly higher specificity than its base selector, so source-order change cannot regress any state.
2. **Made interactions.css LIVE.** It was dead CSS — index.html only loads ui/app.css and app.css only `@import`ed tokens.css, so nothing in interactions.css ever reached the browser. Added `@import "interactions.css";` to app.css (line 2). This ALSO corrects a stale goal-1 claim that interactions.css was "made live via @import" — it was not actually imported until now.
3. **Snapped off-scale gaps** onto the documented spacing scale {4,8,12,16,24}: app.css x10 (3->4, 5->4, 6->8 x7, 10->8, 18->16), cockpit-risks.css x2 (6->8, 10->8), cockpit-trend.css x1 (6->8). `margin:` values left untouched (check counts `gap:` only).
4. **Restored reading measure.** `.msg` had regressed from `max-width:min(78%,75ch)` back to plain `78%`; restored the legitimate 2026-11-20 fix on the live message-bubble selector (not string-gaming). Separately, Pixel removed an orphaned `.readable{max-width:75ch}` today (Forge drift gate) — that removal was correct; the real reading-measure lives on `.msg`.

## Verification
`python memory/designer/design_qa.py` -> **12 passed, 0 failed / 12 total**.
Brace balance OK on all 4 touched files. Import chain: index.html -> ui/app.css -> @import interactions.css (live).

## Files touched
ui/app.css, ui/interactions.css, ui/cockpit-risks.css, ui/cockpit-trend.css

Supersedes: evidence-design-qa-gate-fix-2026-11-26.md (6/6), HOT-NOTES "4/7" claim.