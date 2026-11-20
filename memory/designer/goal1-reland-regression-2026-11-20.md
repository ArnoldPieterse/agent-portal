# Goal #1 re-land (regression found + fixed) - 2026-11-20

Status: verified (live files, not just evidence claims)

## What was wrong
Prior pass recorded goal #1 as wired (pin advanced to 195530265ef0), but the mirror
cycle had REVERTED index.html/app.css back to the old pinned state. Fresh check this
pass showed: index.html did NOT load interactions.js, app.css did NOT @import
interactions.css, and all 16 ad-hoc :hover rules were back in app.css. The evidence
leaves were accurate at write-time; the live files regressed.

## Fix (this pass)
- ui/app.css: added `@import "interactions.css";` after tokens import; removed the 16
  ad-hoc :hover/.on rules (all duplicated in interactions.css PORTAL INTEGRATION).
- index.html: re-added `<script src="ui/interactions.js">` before core.js.
- Pin advanced SAME turn: 815d64fa70b5 -> 195530265ef0 (memory_mirror.py PIN_FILES);
  backup memory/designer/index_html_CANONICAL_195530265ef0_2026-11-20x.html.

## Acceptance (now true in LIVE files)
- [x] >=6 patterns defined in ui/interactions.css (.i-hv/.i-focus/.i-press/.i-drag/.i-scroll/.i-skel)
- [x] All interactive elements use the system (interactions.js loaded; PORTAL INTEGRATION covers all portal selectors)
- [x] No ad-hoc :hover outside interactions.css (app.css=0; other live css=0)

## Verification
- design_qa.py check #4 "no ad-hoc :hover in app.css" = PASS (overall 9/12; the 3 fails
  are pre-existing goal-#5 typography/spacing items, untouched here).
- Ledger: `goal_ledger.py --record designer 1` -> line 5 (verified:) marker. Designer now 4/10 reached.

## Note for next cycle
The shared hot note "all 10 goals verified / do not re-probe" is STALE — the ledger (SSOT)
shows open goals with real gaps; several prior evidence leaves outlived their live-file state
due to mirror reverts. Trust the ledger + a fresh file check, not the header.
