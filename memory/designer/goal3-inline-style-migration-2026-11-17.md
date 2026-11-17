# Goal #3 — Component abstraction: JS-generated inline style= migrated (2026-11-17)
Date: 2026-11-17 (Studio seat, auto-loop pass)
Extends: goal3-component-abstraction-2026-11-16.md (that pass = static index.html; this pass = dynamic JS markup)

## State found at start of pass
- index.html already had 0 inline style= (prior pass migrated the 26 static ones to utility classes in ui/app.css).
- Residual: 6 inline style= in JS-generated chat/panel markup — ui/core.js x5, ui/uploads.js x1.

## This pass — zero real inline style= across ALL UI source
Fixed-layout -> named classes (appended to ui/app.css utility section):
- `.agents-line{margin-left:var(--sp-16)}`  (fleet host "agents:" indent)
- `.mq-item{margin:2px 0}`                   (merge-queue entry row)
- `.btn-mq{padding:1px 8px;font-size:var(--fs-11)}`  (merge-queue restore button)
Dynamic per-agent / per-status color -> token custom-props set via JS `el.style.setProperty` (no style= literal in markup):
- `.msg .who{color:var(--c,var(--dim))}`, `.aev .an{color:var(--c,var(--dim))}`
- `.mh-card{border-color:var(--bc,var(--line))}`

## Verification (ran this pass)
- `findstr /S /C:"style=" index.html ui/core.js ui/uploads.js` -> only CSS *comment* matches; **0 real style= attributes**.
- Named goal#3 selectors (.msg/.panel-head/.btn-primary/.badge-status/.input-bar): 0 style= (4 of them don't exist as classes).
- design_check.py: new rules are token-pure (no raw hex); #ccc fallback replaced with var(--dim). NOTE: it still reports 5 PRE-EXISTING hard violations (dark-mode/theme-toggle = goal#2, reduced-motion guard = goal#4, .status-dot = goal#6) — mirror-reverted other goals' work, OUT OF SCOPE for this pass.

## Acceptance vs goal #3
- "grep shows zero style= on those selectors" -> MET (all 5 named + across UI source).
- "HTML line count drops >=20%" -> MET earlier (index.html 91KB->10.3KB split).
- RESIDUAL OPEN: the "extract as named classes" verb — .panel-head/.btn-primary/.badge-status/.input-bar were never created under those names (design uses #actHead/#fleetHead/.btn/etc.). Inline-style half is DONE; canonical component-class naming is the remaining sub-item.
