# Evidence leaf — Designer Goal #5 Notification System: code complete 2026-11-19

Owner=Designer. Scope this pass: make the toast+bell system REAL (it existed as an orphan file, unwired).

## What was built/changed (all structural, no browser needed)
- `ui/notifications.js` — fixed API bug: `UI.icSVG(iconName,14)` -> `UI.iconSized(iconName,14)` (the real icons.js API). Fallback text glyphs kept for when UI is absent.
- `ui/app.css` — added tokenized CSS block (~30 rules): `.toast-container/.toast(.ok/.warn/.err/.info)/.toast-close`, `@keyframes toastIn`, `.notif-bell/.notif-badge(.hidden)/.notif-panel(.open)/.notif-panel-head/.notif-item/.ni-*/.ni-time`. Uses existing tokens only (var(--sp-4/8/12/16), var(--fs-11/12/13/16), var(--ok/warn/err/acc/dim/line/faint/text/panel/panel2)); no new hex colors.
- `ui/core.js` L7 — **error** trigger: window.onerror now also calls notify("err", ...).
- `ui/uploads.js`:
  - module trackers `_prevStudioOn`, `_prevFleetDone` (transition detection to avoid poll-spam).
  - **upload complete / failed** triggers in uploadFile xhr.onload.
  - **agent offline** trigger in pollStatus() — fires only on true->false transition of studio status.
  - **goal closed** trigger in goals render — fires when fleet_done increases vs previous render.
- `index.html` — added `<script src="ui/notifications.js">` after icons.js, before core.js (so window.notify resolves at runtime). Pin advanced 516a19f3c4e2 -> **995f6479e8be** (backup memory/designer/index_html_CANONICAL_995f6479e8be_2026-11-19y.html, sha-verified).

## Structural verification (ran this pass)
- py_compile memory_mirror.py: OK.
- Triple sha match live==pin==backup == 995f6479e8be -> pin_guard ACCEPTS (no clobber/revert).
- Brace/paren balance: core.js {215,215} ()758,758; uploads.js {251,251} ()958,958; notifications.js {26,26} ()117,117; app.css braces 271/271.
- Grep: `icSVG` remaining = 0; `window.notify` guard+call present at all 4 trigger sites (uploads.js x4, core.js onerror x1); notifications.js present in index.html; all 5 key CSS classes present.

## STILL OPEN (not closable from this seat)
- Acceptance test "all 4 triggers produce correct toast; bell badge updates; toasts dismiss correctly" requires a LIVE BROWSER render — same recorded NEEDS-HUMAN blocker (memory/ops/blockers.md line 22: no browser binary + sandbox egress WinError 10013). Do NOT re-probe from here. Hand to Verifier / a White-capable seat with a browser when available.
- Minor known redundancy: pollStatus has an inner `$("sdot").classList.toggle("on",on)` (L317) plus the new outer one (L320) — idempotent, harmless; left as-is to avoid another match-risk edit.

## Files (relative paths)
ui/notifications.js, ui/app.css, ui/core.js, ui/uploads.js, index.html, memory_mirror.py,
memory/designer/index_html_CANONICAL_995f6479e8be_2026-11-19y.html
