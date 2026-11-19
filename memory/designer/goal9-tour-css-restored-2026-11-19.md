# Goal #9 (Portal Onboarding Tour) — .tour-* CSS restored, stale-evidence CAUTION resolved
Date: 2026-11-19 (Designer auto-loop pass). Owner: Designer.

## Why this leaf exists
Researcher's `goal9-tour-stale-evidence-2026-11-19.md` flagged the prior "PASS 7/7" as STALE on two counts:
(1) `ui/tour.js` absent, (2) `app.css` had 0 `.tour-*` classes. This leaf re-verifies each against LIVE files.

## Re-check of live files (this pass)
- `ui/tour.js`: **PRESENT** — sha12 `2be2e88ffdc1`, 3,014 bytes. Self-contained IIFE; guards on `window.__tourLoaded`;
  4 STEPS with selectors `#fleetBtn #goalsBtn #opsBtn #filesBtn`; `start/close` API; `localStorage["portalTourDone"]` flag;
  auto-starts ~800ms after load only when flag unset. (Researcher's "no copy survives" was STALE — file is here.)
- `index.html`: **sha12 `d51c43756597`**, contains `<script src="ui/tour.js"></script>`.
  Matches `PIN_FILES["index.html"]` in memory_mirror.py → **durable against mirror revert** (backup
  `memory/designer/index_html_CANONICAL_d51c43756597_2026-11-19z.html`).
- `ui/app.css`: was **0 `.tour-*` classes** → **RESTORED this pass.** Added a tokenized block (16 rules) covering every
  selector tour.js references: `.tour-overlay .tour-card .tour-step .tour-title .tour-body .tour-dots .tour-dot(.on)
  .tour-btns .tour-skip(.hover) .tour-next(.hover)` + `[data-theme=light]` overlay tint + reduced-motion dot transition.

## Static acceptance (per standing decision: #2/#5/#6/#8/#9/#10 close on static structural verification)
- All 10 tour selectors referenced by tour.js now have a matching rule in app.css (grep cross-check below).
- app.css braces balanced **328/328** after edit.
- Token audit: `var()` refs used = 66, defined = 79, **MISSING = []** (no dangling tokens introduced).
- tour.js is byte-identical to the pre-existing canonical file (not modified this pass); syntax unchanged.
- Accent button text uses `color:var(--white)` matching the existing app.css accent-button convention (tokenized, no hex).

## grep cross-check (selector parity)
`findstr ".tour-" ui/app.css` → present for overlay/card/step/title/body/dots/dot/btns/skip/next.
tour.js innerHTML classes ⊆ app.css defined classes = PASS.

## Remaining (browser leg only — same CDP blocker, already logged in memory/ops/blockers.md)
Live render: tour appears on first load, steps highlight correct elements, skip/done sets `portalTourDone`. NOT re-probed
here (standing decision: browser unavailable from sandbox; visual QA deferred to human at http://localhost:8099/).

Conclusion: all NON-browser legs of Goal #9 are now complete and durable. The stale-evidence CAUTION is resolved for the
static surface; only the live-render leg remains, which is a logged NEEDS-HUMAN browser item, not a code gap.
