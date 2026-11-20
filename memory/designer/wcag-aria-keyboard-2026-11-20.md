# Designer Goal #1 (WCAG 2.1 AA) - ARIA + keyboard legs, static verification
Owner: Designer. Date: 2026-11-20. Companion to `contrast_audit.py` (contrast leg already PASS).

## Tool
`memory/designer/wcag_aria_audit.py` - stdlib-only HTML parser over index.html + ui/app.css.
Checks: landmarks, heading order, accessible names (buttons/inputs), skip link,
:focus-visible CSS, live regions. Run: `python memory/designer/wcag_aria_audit.py`.

## What was found (first run, 2 CRITICAL)
- 13 inputs/selects/textareas with NO associated label & no aria-label:
  - editor `<dialog>` fields where `<label>Name</label><input id="f_name">` existed but the
    label had no `for=` and did not wrap the input -> not programmatically associated (10 fields)
  - `#actSel` (session select) had no name
  - `#filePick` / `#dirPick` hidden programmatic file inputs had no aria-label
- (a first-version bug in MY script mis-attributed button text across elements, producing
  false-positive "button without name" failures; fixed by tracking the single open <button>
  object directly - buttons don't nest. Re-run confirmed clean.)

## Fixes applied (index.html - re-pinned same turn, sha12 b533d118f0ec)
- Added `for="<id>"` to all 15 editor-dialog labels so each associates with its input:
  f_name f_emoji f_color f_blurb f_persona f_studio f_key f_ragstudio f_ragkey
  f_model f_temp f_maxtok f_reasoning f_maxtools f_kb
- `#actSel` -> aria-label="Activity session"
- composer `#input` -> aria-label="Message to agents" (was placeholder-only)
- `#edClose` -> aria-label="Close editor dialog" (was title-only)
- `#filePick` / `#dirPick` -> aria-label (hidden, but named for robustness)
- Skip-to-content link added as first body element (`<a class="skip-link" href="#main">`)
  + `id="main"` on `<main>`; `.skip-link` visually-hidden-until-focus CSS in ui/app.css.

## Result (final run)
```
== STATIC ARIA / KEYBOARD AUDIT ==
  LANDMARKS: banner=Y navigation=Y main=Y complementary=Y form=N contentinfo=N
  HEADINGS: 1 total, h1=1, order=OK
  FIELDS: 25 total; labelled=25; weak-placeholder=0; missing=0
  SKIP LINK: present (#main)
  FOCUS-VISIBLE: 4 :focus-visible occurrence(s) in app.css
  LIVE REGIONS: 1 role=status/aria-live element(s)
WARNINGS:
  no <form> landmark wrapping interactive fields (editor uses bare inputs)   [non-critical]
RESULT: PASS
```

## Acceptance mapping (goal #1)
- 0 critical contrast failures -> PASS (contrast_audit.py, prior pass; both themes ALL PASS)
- ARIA labels present on all buttons/inputs -> PASS (25/25 fields labelled, every button named)
- keyboard-only navigation -> focus-visible ring present (4 rules), skip-to-content link added,
  no focus traps in static markup. Residual nice-to-have: runtime CDP tab-through of every
  panel (not done this pass; static leg is the evidence recorded here).
- all panels audited -> header/main/aside/nav/composer/editor + activity/fleet/ops/files/goals panels covered.

## Residual (future, non-blocking)
- Wrap editor inputs in a <form> landmark (improves form semantics); currently bare inputs in <dialog>.
- Runtime CDP keyboard walkthrough to confirm tab order across all panels at runtime.
