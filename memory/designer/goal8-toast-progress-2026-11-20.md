<!-- PROVENANCE agent=designer created=2026-11-20 trigger=auto-loop -->
# Goal 8 - Notification/Toast Design: Progress Evidence

## What exists (pre-existing, re-verified this pass):
- **ui/notifications.js** (2824 bytes) - full toast + bell system:
  - 4 types: ok (green), warn (amber), err (red), info (blue/accent)
  - Auto-dismiss TTL=5000ms [PASS]
  - Stackable, MAX=4 visible (first removed on overflow) [PASS]
  - Dismissible by click (close button per toast) [PASS]
  - Bell icon + unread badge + notification panel (last 8 items) [PASS]
- **ui/app.css** lines 310-331 - full CSS for toasts, bell, panel, items
- Loaded in index.html BEFORE core.js (correct order: notifications -> icons -> interactions -> core)

## Real usage sites in core.js (>=3 required):
1. Line 7: window.onerror handler -> notify("err", "JS error: ...")
2. Line 395: fleet refresh -> notify("warn", "Agent host X is offline")
3. Lines 514-528: self-test mode + "notify" demo mode -> ok/warn/err

## Gap fixed this pass (2026-11-20):
- Added .toast.info{border-left-color:var(--acc);} to app.css (was missing - info type had no visual distinction)
- Added .notif-item.n-info{border-left:3px solid var(--acc);} to app.css (matching panel item style)

## Remaining for full closure:
- None significant. All acceptance criteria met:
  - [x] >=4 toast types implemented (ok/warn/err/info with distinct colors)
  - [x] Stacking works (MAX=4, overflow removes oldest)
  - [x] Auto-dismiss timer correct (5000ms + 250ms leave animation)
  - [x] Used in >=3 real scenarios (error handler, fleet offline, self-test)

## Acceptance test:
- Open portal, trigger JS error -> red toast appears bottom-right, auto-dismisses ~5s
- Kill a host process -> amber "Agent host X is offline" toast
- Run ?mode=notify URL param -> 3 toasts + bell badge increments
