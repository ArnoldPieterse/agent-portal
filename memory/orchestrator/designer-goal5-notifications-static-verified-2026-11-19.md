# Designer Goal #5 (Notification System) — static-structural closure, Orchestrator assist 2026-11-19

**Action:** option-(c) contribution (Orchestrator at 100% own goals). Verified + closed a stale-open goal whose build work was complete but never recorded in the ledger.

**Standard applied:** `memory/ops/browser-acceptance-workaround.md` — for sandbox seats, static structural verification IS acceptable closure evidence; live-browser visual QA deferred to the human's own browser at http://localhost:8099/. (Reaffirmed in `memory/orchestrator/browser-blocker-reconciliation-2026-11-19.md`; do NOT re-probe Chrome/Edge headless from sandbox.)

## Acceptance test vs live files (all PASS structurally)
Module: `ui/notifications.js` (2687 chars, IIFE "use strict" + `window.__notifLoaded` idempotency guard). Loaded at `index.html` L160 (before icons.js L161, core.js L162).

| Criterion | Evidence (file:line) |
|---|---|
| Toast top-right | `.toast-container{position:fixed;right:var(--sp-16);top:var(--sp-16)…}` — ui/app.css:287 |
| Auto-dismiss 5s | `TTL=5000` + `setTimeout(dismiss(t),TTL)` — notifications.js notify() |
| Stackable | `MAX=4`; `while(c.children.length>=MAX)c.firstChild.remove()` |
| Bell + unread badge | `ensureBell()` builds `#notifBell` button (aria-label) + `#notifBadge` span; `renderBadge()` sets count, `9+` cap, toggles `.hidden` at 0 |
| Trigger: goal closed | ui/uploads.js:363 `window.notify("ok","Goal closed on "+a.agent…)` |
| Trigger: agent offline | ui/core.js:382 `window.notify("warn","Agent host "+h.host+" is offline")` |
| Trigger: upload complete | ui/uploads.js:24 `window.notify("ok","Upload complete: "+u.rel)` |
| Trigger: error | ui/core.js:7 (window.onerror) + ui/uploads.js:26 (upload failed) → `notify("err",…)` |
| Toasts dismiss correctly | `dismiss()` adds `.toast.leaving` (CSS transition) then `t.remove()` after 250ms; auto via TTL timeout + manual via × button onclick |
| Load-order safe | bell icon `ic=(window.UI&&UI.icon)?UI.icon('settings'):''` computed LAZILY inside `ensureBell()`, wrapped in try/catch — runs on first trigger, well after icons.js (L161) loads. No top-level UI.icon call. |
| Structure | braces 20/20, parens 84/84 balanced; CSS uses design tokens only (--sp-*/--panel/--line/--ok/--warn/--err/--fs-12/--lh-base/--br-*); print media hides .toast-container/.notif-bell/.notif-panel (app.css:332) |

## Notes / honest caveats
- HOT NOTES said "SVG bell+close icons": bell IS an SVG (`UI.icon('settings')`), but the toast close glyph is a text `×` (not SVG). Does NOT affect Goal #5 acceptance (requires dismiss works, which it does). Minor hot-note inaccuracy only.
- The ONLY unmet leg is live-browser rendering of toasts/badge — explicitly deferred to human browser per standing decision. Not a sandbox-closure blocker.

## Verdict
Static-structural PASS on 10/10 acceptance criteria → closed under the documented sandbox standard. Recorded via goal_ledger --record designer 5.
