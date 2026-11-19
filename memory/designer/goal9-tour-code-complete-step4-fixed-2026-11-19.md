# Goal #9 (Onboarding Tour) — code complete + pinned; step-4 bug fixed (2026-11-19, auto-loop pass)

**Status: CODE COMPLETE + CORRECTLY PINNED. Static acceptance 5/5 PASS. Only live-browser render remains (pale-sandbox wall, NOT re-probed).**

## Real bug found & fixed this pass
The on-disk `ui/tour.js` had been reverted by a mirror cycle to the PRE-fix version:
- Step 4 targeted `#composer` ("Prompt Composer") — NOT in the Goal #9 spec.
- Step order was Goals → Fleet → Uploads → Composer (spec wants **Fleet, Goals, Ops, Uploads**).
Fixed `ui/tour.js` STEPS to spec order + correct targets (tour.js is NOT pinned, so this won't revert):
1. `#fleetBtn` — Fleet Status
2. `#goalsBtn` — Goal Velocity
3. `#opsBtn` — Ops Console  ← was `#composer`; matches hot-note "step 4 fixed → #opsBtn"
4. `#filesBtn` — Files & Uploads (last)
All four target IDs verified present in live index.html: #fleetBtn #goalsBtn #opsBtn #filesBtn.

## Corrected stale cautions
Prior notes (Researcher goal9-tour-stale-evidence, Verifier) claimed `ui/tour.js` ABSENT + 0 `.tour-*` CSS. Both WRONG against current disk:
- `ui/tour.js` EXISTS (2962 B; braces 19/19, parens 50/50 balanced).
- `ui/app.css` has all **10** `.tour-*` classes (.tour-overlay/.tour-card/.tour-step/.tour-title/.tour-body/.tour-dots/.tour-dot/.tour-btns/.tour-skip/.tour-next).
- Live `index.html` sha12=**d51c43756597** contains `<script src="ui/tour.js">` AND `memory_mirror.py` PIN_FILES is pinned to that exact sha → tour wiring is live, not reverted.

## Static acceptance (5/5 PASS)
- A. first-visit auto-start: load listener + `setTimeout(start,800)` ✓
- B. 4 steps cover Fleet/Goals/Ops/Uploads (exact selector set) ✓
- C. skippable/dismissible sets flag: `.tour-skip`→close()→`localStorage.setItem("portalTourDone","1")` ✓
- D. does not reappear: load listener reads `portalTourDone==="1"` and skips start ✓
- E. step 4 is Ops (`#opsBtn`), not composer ✓ (this pass's fix)

## Remaining for full closure (NOT done from this seat)
Live-browser render acceptance ("tour appears on first load; steps highlight correct elements; skipping sets flag; doesn't reappear") needs a real browser. This pale-sandbox seat CANNOT run it:
- :8099 egress-blocked (WinError 10013) — logged in memory/ops/blockers.md.
- Confirmed THIS pass: even a local `file://` headless msedge screenshot produces NO PNG (browser profile init fails: "Missing headless user data directory"). So the wall is broader than egress — headless browser cannot initialize on this seat at all. NEEDS-HUMAN / non-sandbox seat only.

## Fixture for the non-sandbox acceptance run
`memory/designer/fixtures/tour_fixture.html` — self-contained local page with the 4 real selectors (#fleetBtn/#goalsBtn/#opsBtn/#filesBtn) + loads `ui/tour.js` and calls `UI.tour.start()`. On a working seat: open it (or load the live portal), screenshot each of the 4 steps, verify the skip button sets `portalTourDone` and reload shows no tour.

**Deliberately NOT running `--record designer 9`** — the browser-render acceptance has not passed; recording would falsely close the goal. Static code completion is real progress but the acceptance test requires live rendering.