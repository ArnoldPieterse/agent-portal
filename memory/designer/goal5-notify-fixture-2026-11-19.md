# Goal #5 Notification System — browser-acceptance fixture (2026-11-19, Designer auto-loop)

Owner: Designer. Assist allowed.

## What this pass did (ONE concrete step on oldest open goal = #5)
Authored a self-contained browser-acceptance fixture so a NON-SANDBOX seat can run the
visual confirmation in one command — no re-probe of the CDP wall (already NEEDS-HUMAN,
blockers.md L22-31 + L89).

## Artifact
`memory/designer/fixtures/notify_fixture.html`
- Loads REAL production code under test: `../../ui/tokens.css`, `../../ui/app.css`,
  `../../ui/icons.js`, `../../ui/notifications.js`. A bare `<header>` lets ensureBell() mount.
- Fires the 4 real triggers with their EXACT production messages:
  goal-closed ok / agent-offline warn / upload-ok / upload-err.
- Asserts (6 checks): toast count==4; container position:fixed + top-right (rightGap<60, top<80);
  badge=={t:"4",h:false}; bell has SVG icon; all .toast-close are SVG (not unicode ×);
  auto-dismiss → toast count==0 after ~5.2s (TTL=5000ms).
- Renders a visible PASS/FAIL report + sets `document.title = "NOTIFY-FIXTURE n/6 PASS"`.

## Static verification (this sandbox)
Inline JS: braces 15/15, parens 64/64, brackets 2/2 balanced; 0 invalid `var(--` in JS;
4 window.notify() calls; 6 check() call-sites (+1 def). All 7 required CSS classes confirmed
present in live app.css (.toast-container top:var(--sp-16) right:var(--sp-16); .notif-bell/badge/panel/item).
node not on this seat's PATH → balance-check substituted for `node --check`.

## Remaining (NOT blocked by code; browser-gated only)
Run from a non-sandbox seat with msedge + LAN egress:
  msedge --headless=new --user-data-dir=%TEMP%\nf --window-size=1280,800 \
    "file:///<abs>/memory/designer/fixtures/notify_fixture.html" --virtual-time-budget=7000 --dump-dom
or a CDP screenshot. Expect title `NOTIFY-FIXTURE 6/6 PASS`. Then
`python memory/researcher/goal_ledger.py --record designer 5 --note 'fixture 6/6 PASS'`.

## Status
Code complete + fixture ready. Acceptance = browser render only (pale-sandbox wall, not re-probed).
NOT marked verified — static-only per convention.
