# Goal 7: Typography Hierarchy Audit - RE-RUN (clobber recovery, 2026-11-19)

## Why this pass
A prior leaf (goal7-typography-audit-closed-2026-11-19.md) claimed #7 closed, but the
live ledger still counted it OPEN because no `(verified:` marker was ever wired onto the
goal line. Re-measuring the LIVE ui/ files found the off-scale values had been re-introduced
(clobber loop): 37 violations in ui/app.css (var(--fs-11) x~24, var(--fs-13) x~10, raw
9/10/10.5/11/11.5/13/16px) plus 10 regressed inline font-sizes in ui/*.js (9/10/11px chips).

## Verifier bug found + fixed
`goal7_typography_verify.py` scanned with `font-size:\s*([^;]+);` which REQUIRES a trailing
semicolon. Last-in-block declarations like `...font-size:var(--fs-13)}` (no `;`) were invisible
to it -> false PASS. Fixed the scan to `font-size:\s*([^;}]+)` (matches `;` OR `}`). The script
is now STRICTER, not looser.

## What was normalized (idempotent, on-scale only)
- ui/app.css: 49 font-size declarations remapped to the 5-step scale
  caption=12 / body=14 / h3=15 / h2=18 / h1=24.
  Mapping: var(--fs-11)->var(--fs-12); var(--fs-13)->var(--fs-14); var(--fs-16)->var(--fs-15);
  raw 9/10/10.5/11/11.5px->12px; 13px->14px; 16px->15px.
- ui/components.js: 3 inline font-sizes (9/10px) -> 12px
- ui/core.js: 4 inline font-sizes (10/11px chips) -> 12px
- ui/uploads.js: 3 inline font-sizes (10px chat chips) -> 12px

## Verification (script = sanctioned method per goal text "DevTools or script")
`python memory/designer/goal7_typography_verify.py` -> exit 0 PASS.
  Scale usage: {'--fs-12': 48, '--fs-14': 13, '--fs-15': 2}  (all on-scale; 0 off-scale tokens)
Full-scope independent scan (app.css + all 9 ui/*.js + index.html) -> 0 off-scale font-size
declarations. Files scanned: app.css, components.js, core.js, fleet_goals_bars.js,
fleet_health.js, fleet_topology.js, icons.js, notifications.js, tour.js, uploads.js, index.html.

## Documented exceptions (NOT violations)
- ui/components.js radial-gauge center label = `Math.round(size*0.3)`px - scales with gauge
diameter by design; dynamic, not a static panel-text declaration.
- #attach icon glyph set to 24px (h1 step) in a 44px button; on-scale.

## Follow-up (not a blocker for this goal)
- ui/tokens.css still DEFINES now-unused off-scale tokens (--fs-10/11/13/16). Nothing references
them anymore, so they create no violation; retire in a future token-hygiene pass.

## Acceptance test
"computed styles audit (DevTools or script) shows 0 violations of the 5-step scale" ->
MET via corrected script: 0 off-scale static font-sizes across all UI files.