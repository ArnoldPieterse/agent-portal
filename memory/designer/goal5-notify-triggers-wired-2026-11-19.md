# Goal #5 — notify() trigger wiring (code-level) COMPLETE 2026-11-19 (Designer, auto-loop pass)

## What was the gap
`window.notify(type,msg)` was DEFINED in ui/notifications.js but had **ZERO call-sites** across the
whole UI (grep `window.notify(` -> only the definition). So none of the 4 required triggers fired.

## What I did (no browser needed — pure code wiring + verification)
Added guarded calls `if(window.notify)window.notify(type,msg)` at each event site:

| #5 trigger      | type | file          | location / condition                                  |
|-----------------|------|---------------|-------------------------------------------------------|
| goal closed     | ok   | ui/uploads.js | goalsLoad(): on fleet_done increase vs _prevFleetDone  |
| agent offline   | err  | ui/uploads.js | pollStatus(): online->offline transition (_prevOnline) |
| upload complete | ok   | ui/uploads.js | xhr.onload: HTTP 200/201 (bonus 'err' on upload fail)  |
| error           | err  | ui/core.js    | window.onerror: global JS errors                       |

- Added module-scope state vars `_prevOnline` / `_prevFleetDone` (each declared once).
- pollStatus restructured to lift `on` into function scope via `__on`/`__off`; the original
  `const on=!s.error;` and the status-text ternary are byte-for-byte UNCHANGED (verified present).

## Verification (in-sandbox, no browser)
- 5 real call-sites now exist: core.js(1) + uploads.js(4). All 4 required triggers covered.
- Per-line brace/paren balance of every inserted line = balanced (manual analysis; whole-file home-grown
  parser is unreliable here — it false-flags the working core.js, so not used as evidence).
- `const on=!s.error;` intact + status ternary intact => existing UI behaviour preserved.

## NOT yet closed (honest)
Acceptance test = "all 4 triggers produce correct toast; bell badge updates; toasts dismiss correctly"
is a LIVE-BROWSER check. Still pending — same recurring NEEDS-HUMAN blocker already logged in
memory/ops/blockers.md ("Live-browser verification unavailable from this sandbox seat"). Do NOT re-probe.
This leaf records the code-wiring sub-milestone only; do NOT run `--record designer 5` until the browser leg passes.

Files touched: ui/core.js, ui/uploads.js (both non-pinned; index.html untouched).
