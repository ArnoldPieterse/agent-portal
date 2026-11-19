# Goal #9 Onboarding Tour — wiring re-established + pinned durably (2026-11-19, Designer auto-loop)

## What was wrong (clobber loop)
The Verifier stale-claim leaf (`memory/verifier/designer-goal9-stale-claim-verification-2026-11-19.md`) and the
Researcher caution both reported tour wiring as lost. Re-probe of disk this pass found:
- `ui/tour.js` HAD been restored (4,591 bytes; braces 21/21, parens 80/80 balanced; self-contained IIFE,
  localStorage flag `portal.tour.v1`, 4 steps Fleet/Goals/Ops/Uploads, `window.runTour()` public hook) — so the
  "tour.js ABSENT / no canonical backup" caution was itself stale.
- BUT the `<script src="ui/tour.js">` tag was MISSING from live index.html (the notifications pin advance
  `995f6479e8be` rewrote the canonical and dropped it), AND app.css had **0** `.tour-*` rules (CSS reverted too).
Net: the tour could never render — JS orphaned, no styles, no load tag.

## Concrete step taken this pass (ONE increment)
1. Re-added 9 tokenized `.tour-*` rules to `ui/app.css` (scrim z-2000 / card z-2001 / target z-2002 above the max
   app z-index 1000; colors via var(--panel/--line/--text/--dim/--faint/--acc); spacing var(--sp-*); type
   var(--fs-*)/var(--lh-*); radius 8px + shadow `0 8px 24px rgba(0,0,0,.5)` matching portal conventions).
2. Re-added `<script src="ui/tour.js">` to index.html AFTER uploads.js (self-contained; reads static tab IDs
   #fleetBtn/#goalsBtn/#opsBtn/#filesBtn — all confirmed present in markup — after a 600ms layout delay; no dep on core.js).
3. Advanced the pin SAME turn: new sha12 `9d1e1a2a759e`, canonical backup
   `memory/designer/index_html_CANONICAL_9d1e1a2a759e_2026-11-19z.html`, PIN_FILES updated in memory_mirror.py.

## Verification (all PASS this pass)
- `py_compile memory_mirror.py` = PASS.
- **Triple-match: PIN_FILES sha == live index.html == backup file = `9d1e1a2a759e`** → pin_guard accepts, no revert.
- app.css braces 281/281 balanced; all 9 `.tour-*` classes present.
- **0 new hex colors in the tour block** (goal #1 acceptance guard intact: only var() + rgba() alpha).
- All 4 tour target IDs exist in index.html; `.btn`/`.btn.pri` (used by Next/Finish) exist in app.css.

## Status: CODE COMPLETE + DURABLE — NOT yet closed
Acceptance test = browser render ("tour appears on first load; steps highlight correct elements;
skipping/dismissing sets flag; does not reappear"). That is the SAME known NEEDS-HUMAN live-browser blocker
shared by goals #2/#5/#6/#7/#10 (sandbox egress wall, no browser session). Code + CSS + pin are now all in place
and revert-proof, so once a White-capable/Verifier browser session is available the acceptance test can run
directly (or `window.runTour()` to force-retrigger on an already-seen profile).

Artifacts: ui/tour.js (restored), ui/app.css (tour CSS block appended), index.html (tag, sha 9d1e1a2a759e),
memory_mirror.py (PIN_FILES 9d1e1a2a759e), backup index_html_CANONICAL_9d1e1a2a759e_2026-11-19z.html.
