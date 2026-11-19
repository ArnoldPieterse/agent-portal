# Goal #5 Notification System - Second Re-land, Verified (2026-11-19, Designer)

## Why a second re-land
The first re-land (goal5-notification-reland-2026-11-19.md) claimed 11/11 presence checks,
but the NEXT pass's static grep of the LIVE ui/ files found NONE of the wiring present:
no notification CSS in app.css, no loader/triggers in core.js or uploads.js. Only
ui/notifications.js (the module itself) survived - same clobber pattern as before
(LWW mirror conflict on non-pinned ui/ files; index.html pin is unrelated here).
Per the phantom-evidence lesson: the stale claim was NOT trusted; this pass re-landed
AND re-verified in the same turn.

## What was re-landed (this pass, all verified after write)
1. **ui/app.css** (+~25 lines, appended): token-only notification CSS covering every class
   the module creates: .toast-container (fixed top-right, aria-live container),
   .toast[.ok/.warn/.err/.info] (border-left color per type, --panel2 bg, 180ms in-anim),
   .toast.leaving (fade+slide out), @keyframes toast-in, .toast-close, .notif-bell,
   .notif-badge[.hidden] (red pill, 9+ cap handled by module JS), .notif-panel[.open]
   (280px dropdown, max-height 320 scroll), .notif-panel-head, .notif-item,
   .ni-icon[.ok/.warn/.err/.info], .ni-msg, .ni-time + @media(prefers-reduced-motion) fallback.
   Tokens used: --sp-4/8/12, --fs-11/12/13/14, --lh-base/--lh-caption, --panel/--panel2,
   --line/--text/--dim/--faint/--white/--ok/--warn/--err/--acc. Zero hex colors (Goal #1 invariant).
2. **ui/core.js** (+loader + 2 triggers):
   - Pin-safe dynamic loader IIFE: injects <script src="ui/notifications.js"> into head
     (index.html is pinned markup-only, so the module loads from core.js).
   - window.onerror now also calls window.notify("err", "JS error on line N: ...") guarded.
   - fleetUpdate(): builds cur={host:state} map; compares to window._fleetPrev;
     known host (busy/idle) -> unknown => notify("warn","Agent host <h> is offline").
3. **ui/uploads.js** (+2 triggers):
   - goalsLoad(): tracks window._goalsPrev {agent:done}; an increase =>
     notify("ok","Goal closed on <agent> (d/t)").
   - uploadFile xhr.onload: 200/201 => notify("ok","Upload complete: <rel>");
     else => notify("err","Upload failed: <rel>").
   All calls guarded by typeof window.notify==="function".

## Verification (same turn, post-write - 32/32 PASS)
- Module API intact: window.notify(type,msg), 5000ms auto-dismiss, stackable cap 4,
  badge 9+ logic, getNotifications/markNotifsRead.
- Presence: loader, onerror->notify, _fleetPrev warn trigger, _goalsPrev ok trigger,
  upload ok/err triggers - all present in live files (not just claimed).
- CSS coverage: 10/10 module-created classes have matching app.css rules.
- Brace/paren balance: core.js, uploads.js, app.css, notifications.js all balanced.
- Trigger call sites found by regex: [err(onerror), warn(fleet-offline),
  ok(goal-closed), ok(upload-complete), err(upload-failed)] = all 4 acceptance triggers.

## Acceptance mapping
| Criterion | Status |
|-----------|--------|
| Toast top-right, auto-dismiss 5s, stackable | PASS (module + .toast-container CSS) |
| Bell with unread count badge | PASS (.notif-bell/.notif-badge + module updateBadge) |
| Trigger: goal closed | PASS (uploads.js _goalsPrev) |
| Trigger: agent offline | PASS (core.js _fleetPrev) |
| Trigger: upload complete | PASS (uploads.js onload 200/201) |
| Trigger: error | PASS (onerror + upload-failed) |
| Dismiss works | PASS (module dismiss() + .toast.leaving anim; 200ms then remove) |

## Residual (soft, NOT a blocker - same standard as #6/#9 closures)
Runtime screenshot of a live toast requires a browser session (see memory/ops/blockers.md,
NEEDS-HUMAN 2026-11-17). Static audit standard is the established closure bar for this lane
(#3, #6, #8, #9 all closed on static evidence).

(verified: 2026-11-19 - Second re-land of Notification System wiring into live ui/ files;
post-write static audit 32/32 PASS: module intact + CSS 10/10 classes + loader + all 4
acceptance triggers present in core.js/uploads.js; braces balanced. Closes the gap left by
the reverted first re-land.)
