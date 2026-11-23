# Runbook one-click trigger — token refactor (assist on Builder goal #10)
Date: 2026-11-24 · Lane: Designer · Type: assist / UI hardening

## Context
Builder goal #10 (Cockpit One-Click Runbook Trigger) was verified engine-side (selftest 8/8, runbook_trigger.py). The **UI leg** in `ui/cockpit.js` renderRunbooks() still used hardcoded inline hex + font-size that do not switch with the theme and skip the a11y state system — i.e. it would fail "error state shown" contrast expectations in light mode.

## Defect (before)
- Run button: `background:#2ea36b;color:#fff` (off-palette green, white text low-contrast on bright fill in dark mode).
- Abort button: `background:#e5534b;color:#fff` (off-palette red).
- Meta/progress/error spans: `color:#8a8f98` / `color:#e5534b`, `font-size:11px` — none tokenized, so no dark/light switching.
- No :focus-visible ring, no :disabled visual (JS poked `style.opacity` inline), Abort hidden via inline `display:none`.

## Fix (after)
New scoped block appended to **ui/app.css** (canonical stylesheet, not pinned): `.rb-btn` base (inline-flex, var(--fs-12), var(--sp-4)/var(--sp-8) padding, var(--br-sm)), `:focus-visible{outline:2px solid var(--focus)}`, `:disabled{opacity:.5;cursor:not-allowed}`, `[hidden]{display:none}`, `.rb-btn-run{color/border:var(--ok); hover bg var(--ok-soft)}`, `.rb-btn-abort{color/border:var(--err); hover bg var(--panel2)}`, `.rb-meta{color:var(--faint);font-size:var(--fs-11)}`, `.rb-prog{...var(--dim)}`, `.rb-prog-err{color:var(--err);font-weight:600}`.

`ui/cockpit.js`: buttons now `class='rb-btn rb-btn-run'` / `class='rb-btn rb-btn-abort' hidden`; Abort toggled via `.hidden` (4 sites); removed 5 inline `runBtn.style.opacity` pokes; error spans → `class=rb-prog-err`; meta/empty states → `class=rb-meta`. No markup/behavior change, CSS-only theming + a11y.

## Validation (static)
- cockpit.js bracket balance OK: () 266/266, {} 96/96, [] 23/23.
- app.css brace balance OK: 363/363.
- Every `rb-*` class referenced in JS is defined in app.css (missing: none).
- No stale `runBtn.style.opacity` / `abortBtn.style.display` remain in the runbook block; 4 `abortBtn.hidden` toggles consistent.
- Visual proof: render_html fixture (real token values, exact classes) shows idle / pre-flight-error / running+Abort states correct in BOTH dark and light themes.

## Notes / follow-up (NOT done this pass — separate larger task)
The rest of the cockpit panel (color functions L9-11, CSS-in-JS strings L20-33, bars/gauges L64-102) still uses hardcoded hex. That is a whole-panel tokenization effort; out of scope for a one-step assist. Flagged for a future Designer goal.

Files changed: ui/app.css (+14 lines), ui/cockpit.js (runbook block only). No index.html change → no pin advance needed.