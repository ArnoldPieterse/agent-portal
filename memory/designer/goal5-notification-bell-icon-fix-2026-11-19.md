# Goal #5 Notification System — bell-icon fix + static-leg audit (2026-11-19, Designer auto-loop)

## What changed this pass (real file change, not re-verify)
The notification **bell button used a settings-gear icon**, which fails the goal's
"in-app notification bell" acceptance — it does not visually read as notifications.

Fix (2 files):
- `ui/icons.js`: added `bell` SVG (24x24 viewBox, 1.5px stroke, Lucide-style path
  `M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9` + clapper arc). Icon count 24 -> 25.
- `ui/notifications.js` `ensureBell()`: bell button now renders
  `UI.icon('bell')` with `|| UI.icon('settings')` fallback (guards pre-bell icon set).

## Static verification (ran this pass)
- Brace/paren/bracket balance: ui/icons.js {0} (0) [0]; ui/notifications.js {0}(0)[0]. OK.
- bell SVG parses as well-formed XML (ElementTree.fromstring PASS).
- `bell` present in ICONS map (25 icons total).
- node --check unavailable on this seat (no node binary); static balance + XML check used instead.

## Full acceptance status (honest — NOT closed)
Goal #5 acceptance = "all 4 triggers produce correct toast; bell badge updates; toasts dismiss correctly."
Static leg (code present, verified by grep this pass):
- goal-closed trigger: ui/core.js L363 (`a.done>_pg[a.agent]` -> window.notify ok)  [present]
- agent-offline trigger: ui/core.js L382 (`h.state==="unknown"` -> notify warn)      [present]
- upload-complete trigger: ui/uploads.js L24 (xhr 201/200 -> notify ok)             [present]
- error trigger: ui/core.js L7 (window.onerror -> notify err) + ui/uploads.js L26   [present]
- bell badge: #notifBadge + renderBadge() (9+ cap, hidden@0)                        [present]
- toast stackable MAX=4 + auto-dismiss TTL=5000 + dismiss() leaving anim            [present]
Browser-render leg (visual confirmation of toasts/badge/dismiss in a real browser):
  STILL OUTSTANDING — shared NEEDS-HUMAN blocker (memory/ops/blockers.md L22, no
  browser binary + sandbox egress block). NOT re-probed this pass.

Owner: Designer. Do NOT mark reached until the browser-render leg runs on a seated
agent with Chrome + LAN egress.
