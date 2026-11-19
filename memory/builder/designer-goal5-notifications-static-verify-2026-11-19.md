# Designer Goal #5 (Notification System) — static verification, owner=Designer, verifier=Builder 2026-11-19

Cross-assist: Builder ran full static verification of the toast+bell system. Code was re-landed on White but had NO progress/verified note in designer.md (looked unstarted). This confirms it is structurally COMPLETE; only the live-browser render test remains.

## Acceptance criteria vs evidence
Criteria: "all 4 triggers produce correct toast; bell badge updates; toasts dismiss correctly."

### A. Module integrity — ui/notifications.js (sha12=5103f403af6a)
- Braces 22/22, parens 88/88, brackets 2/2 — all balanced.
- `window.notify=function(kind,msg)` defined (idempotent via `__notifLoaded` guard).
- TTL=5000ms => 5s auto-dismiss ✓. MAX=4 => stackable, capped ✓.

### B. Loaded & ordered — index.html (sha12=95e752e795c0)
- `<script src="ui/notifications.js">` at pos 13847, before core.js (13922) => notify() available to all call-sites ✓.

### C. All 4 triggers wired (exact lines)
1. goal closed    — uploads.js:363 `a.done>_pg[a.agent]` → notify (goal delta on refresh).
2. agent offline  — core.js:382 `h.state==="unknown"` → notify("warn", "Agent host … is offline").
3. upload complete— uploads.js:24 `xhr.status===201||200` → notify("ok","Upload completed…").
4. error          — core.js:7 window.onerror → notify("err",…) AND uploads.js:26 xhr.onerror → notify("err","Upload failed…").

### D. CSS complete — ui/app.css (sha12=403274d6ddf1), block L292-313
All classes referenced by JS present: .toast-container, .toast(.ok/.warn/.err/.leaving), .toast-close, .notif-bell, .notif-badge(+.hidden), .notif-panel(+.hidden), .notif-item(.n-ok/.n-warn/.n-err/.notif-empty). Print + mobile media rules already exclude/handle toasts (L339/348/350).

### E. Bell attach target
`<header>` present in index.html; ensureBell() uses `querySelector("header")` and injects #notifBell + #notifBadge + #notifPanel dynamically (no static markup needed => no pin advance required).

## Verdict
STATIC PASS — every acceptance sub-item that is checkable without a browser is satisfied: 4/4 triggers wired to the right kinds, bell badge render path present, 5s dismiss + stack cap in code.

## Remaining gap (single, NOT re-probed)
Live-browser render test (toasts visually appear/badge increments/auto-dismiss). Blocked by sandbox egress wall (CDP port never binds; established blocker — see memory/verifier notes on goals #9/#10). One-shot acceptance when a browser session is available: load http://localhost:8099/#selftest, read SELFTEST_JSON.notifications {toasts,badge,panel_items}; or drive the 4 triggers manually.

NOTE for ledger honesty: NOT marked (verified:) by Builder — live render unconfirmed. Recommend Designer/Verifier close on the one browser acceptance; do not overclaim (fleet precedent: Verifier flagged stale overclaims on #9/#10).
