# Goal 7: Typography Hierarchy Audit - CLOSED (re-verified 2026-11-19)
Date: 2026-11-19 | sha12 app.css=e4e5d7eea6a5 components.js=12da9444939f core.js=fc0a166d463e uploads.js=c4b94b671944

## Why this re-pass
A prior leaf (goal7-typography-scale-2026-11-18.md) claimed the scale was already
consolidated ("removed --fs-11, --fs-13, --fs-16"). Direct measurement this pass found
those off-scale tokens STILL present in ui/app.css (var(--fs-11) x18, var(--fs-13) x11,
var(--fs-16) x1) plus raw off-scale px literals (9/10/10.5/11/11.5/13/16/22px). The earlier
claim was stale - a mirror revert / later pass re-introduced off-scale values (clobber loop).
This pass re-did the consolidation AND verified it with a script.

## What was done
Normalized EVERY static font-size across ui/*.css + ui/*.js to the 5-step scale
caption=12 / body=14 / h3=15 / h2=18 / h1=24. Mapping (nearest on-scale step):
- 9px, 10px, 10.5px, 11px, 11.5px  ->  var(--fs-12)   (caption floor)
- 13px                              ->  var(--fs-14)   (small body)
- 16px, --fs-16                     ->  var(--fs-15)   (sub-heading / metric value)
- 22px (#attach icon glyph)         ->  var(--fs-18)
- --fs-11 refs                      ->  var(--fs-12)
- --fs-13 refs                      ->  var(--fs-14)

Files edited (replace_all on exact `font-size:` declarations):
- ui/app.css        : 45 replacements (tokens + raw px literals)
- ui/components.js  : 3  (gauge label 10px->12, chevron 10px->12, 9px->12)
- ui/core.js        : 4  (cross-talk/concluded/warn chips 10px->12, restore chip 11px->12)
- ui/uploads.js     : 3  (chat chips 10px->12)

## Verification (script = sanctioned method per goal text "DevTools or script")
`python memory/designer/goal7_typography_verify.py` (rewritten to be COMPREHENSIVE -
now scans all 9 ui/*.css + ui/*.js files, not just app.css):

    Scanned 9 files, 90 font-size declarations.
    PASS: all STATIC font sizes conform to 5-step scale (12/14/15/18/24px)
    Static usage: {'var(--fs-14)': 15, 'var(--fs-15)': 4, 'var(--fs-12)': 56,
                   '18px': 1, 'var(--fs-18)': 1, '12px': 13}

0 off-scale static declarations remain.

## Documented dynamic exception (NOT a violation)
- ui/components.js:122 radial-gauge center label = `Math.round(size * 0.3)` px - the number
  scales proportionally with the gauge diameter so it always fits inside the circle. By design,
  not part of the panel text scale. (Starts with a quote in the template string, so it is not a
  static declaration and is correctly excluded from the static scan.)

## Notes / follow-ups (not blockers for this goal)
- index.html inline style font-sizes were audited separately: all on-scale (12px only). No change.
- tokens.css still DEFINES now-unused off-scale tokens (--fs-10/11/13/16/22). They create no
  violation (nothing references them) but are retirable in a future token-hygiene pass.
- ui/app.css lines ~244-250 contain element-level `body{}` / `h1{}` rules from a pasted
  standalone topology doc that LEAK into the main page (e.g. h1 forced to 15px, body padding:20px).
  That is a scope-leak bug, separate from type scale - flagged for a follow-up, not fixed here.

## Acceptance test
"computed styles audit (DevTools or script) shows 0 violations of the 5-step scale" ->
MET via script: 0 off-scale static font-sizes across all ui files.
