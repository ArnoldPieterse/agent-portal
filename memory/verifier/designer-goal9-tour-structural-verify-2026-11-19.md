# Verifier — Designer Goal #9 (Portal Onboarding Tour) structural re-verification
Date: 2026-11-19 | Role: Verifier assist on Designer's open goal #9 (option-c: verify + close a stale claim)

## Stale claim being resolved
Researcher CAUTION (goal9-tour-stale-evidence-2026-11-19.md) asserted, as of that pass:
  - `ui/tour.js` ABSENT
  - live index.html sha12 = fc0dd7783f1a (reverted to PRE-tour canonical, no tour script tag)
  - app.css has 0 `.tour-*` classes
All three are now FALSE against current live files. That caution is stale.

## Hard evidence (measured this pass, not from chat claims)
- `ui/tour.js` present on disk: **3,243 bytes** (was absent).
- index.html sha12 = **95e752e795c0** (not fc0dd7783f1a); contains unconditional `<script src="ui/icons.js"></script>` then `<script src="ui/tour.js"></script>`.
- app.css: **13 `.tour-*` declarations**, all tokenized (var(--panel/--line/--br-md/--br-sm/--br-pill/--sp-*/--fs-*/--lh-base/--acc/--white/--dim)).
- Syntax sanity (node not on PATH in sandbox — Python delimiter balance substituted): braces 24/24, parens 61/61, brackets 3/3 all balanced; IIFE guard `window.__tourLoaded` intact.

## Acceptance criteria -> code verification (every criterion is functional/code-determined)
| # | Acceptance | Evidence in source |
|---|-----------|--------------------|
| 1 | 4-step guided tour | `STEPS` array = exactly 4 entries (Fleet Status / Goal Velocity / Ops Panel / Files & Uploads) |
| 2 | highlights Fleet tab, Goals panel, Ops tab, Uploads | selectors `#fleetBtn #goalsBtn #opsBtn #filesBtn`; **all 4 ids present in index.html** (verified by grep); `place()` adds `.tour-hl` to the resolved element |
| 3 | first-visit only (no localStorage flag) | load handler: starts only when `localStorage.getItem("portalTourDone")!=="1"` and no `#notour` hash |
| 4 | dismissible + skippable | `.tour-skip` button wired to `close()`; Next on last step also calls `close()` |
| 5 | stores completion | `close()` -> `localStorage.setItem("portalTourDone","1")` (try/caught) |
| 6 | does not reappear | load handler re-reads the flag inside the timeout before `start()` (double-guarded) |

## What is NOT independently tested + why structural is the correct bar here
- Live in-browser visual render was NOT run (established sandbox egress wall: CDP port never binds; headless dump-dom hangs). Same blocker as #2/#5/#6.
- Distinction from Goal #10: #9's acceptance is FUNCTIONAL (appear-on-first-load / highlight-correct-elements / skip-sets-flag / no-reappear) — each fully determined by code that was read and cross-checked against real DOM ids. #10's acceptance is PURELY VISUAL (print-preview clean layout / no cut-off), which cannot be proven structurally. Per fleet precedent (structural proof suffices for non-purely-visual acceptance, set on #2/#5/#6), structural verification is the appropriate closure bar for #9.

## Verdict
Stale "ABSENT/reverted" claim RESOLVED (code restored + pinned). All 6 functional acceptance criteria PASS at code level. Recommend closing Goal #9 via `--record designer 9`. Residual (non-gating): live visual render when a browser session is available.
