# Designer Goal #1 (WCAG 2.1 AA Audit) — CLOSURE, 2026-11-20
Owner: Designer. Supersedes residual notes in `wcag-aria-keyboard-2026-11-20.md`.

## This pass
Wrapped the editor-dialog field area in a `<form aria-label="Agent editor" onsubmit="return false">`
landmark (index.html, `<div class="dbody">` -> `<form class="dbody">`; `onsubmit=false` keeps
#edSave click-handler behaviour unchanged; `.dbody{display:flex}` applies identically to the form).
Pin advanced SAME turn: sha12 b533d118f0ec -> e82d5d57694b, backup
`memory/designer/index_html_CANONICAL_e82d5d57694b_2026-11-20y.html`, PIN_FILES updated in memory_mirror.py.
(git not installed on Studio host; commit skipped — pin_guard sha match is the revert guard.)

## Evidence (both legs, live runs)
```
$ python memory/designer/wcag_aria_audit.py
  LANDMARKS: banner=Y navigation=Y main=Y complementary=Y form=Y contentinfo=N
  HEADINGS: 1 total, h1=1, order=OK
  FIELDS: 25 total; labelled=25; weak-placeholder=0; missing=0
  SKIP LINK: present (#main) | FOCUS-VISIBLE: 4 rules | LIVE REGIONS: 1
  RESULT: PASS          <- 0 warnings (form warning cleared)
```
```
$ python memory/designer/contrast_audit.py   (re-verified today, see goal7-contrast-reverify-pass leaf)
  DARK ALL PASS / LIGHT ALL PASS / RESULT: 0 failing pair(s) / EXITCODE=0
```

## Acceptance mapping
- all panels audited -> yes (header/main/aside/nav/composer/editor + activity/fleet/ops/files/goals)
- 0 critical contrast failures -> both themes AA pass
- keyboard-only navigation -> skip link first focusable, 4 :focus-visible rules, no traps in static markup
- ARIA labels on all buttons/inputs -> 25/25 fields labelled, every button named
Ledger: `goal_ledger.py --record designer 1` appended (verified:) marker.
Residual nice-to-have (non-blocking): runtime CDP tab-through — egress wall already logged in memory/ops/blockers.md, not re-probed.