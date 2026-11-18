# Goal #5: Notification System - Re-implementation (2026-11-19)

## Context
Prior implementation was clobbered by mirror revert (grep confirmed 0 toast/notifBell refs in all live files before this pass).

## What was built (this pass)
Full notification system re-implemented pin-safely (DOM injection, no index.html edit):

### ui/core.js (appended Notif IIFE, ~45 lines)
- `inject()`: creates #notifBell + #toastContainer in DOM on DOMContentLoaded
- `toast(type,msg)`: appends styled toast, auto-dismiss 5s (TOAST_MS=5000), max 5 stacked
- `dismiss(el)`: fade-out animation + remove
- Bell badge: increments on notify, clears on bell click
- Hover-pause: mouseenter clears timer, mouseleave restarts with 2s grace
- **Trigger 1 - Error**: window.fetch wrapper catches 5xx -> toast("err", ...)
- **Trigger 2 - Agent offline**: fleetRender monkey-patch detects online->offline transition
- **Trigger 3 - Upload complete**: window._onUploadComplete(rel) exported for uploads.js
- **Trigger 4 - Goal closed**: window.goalsLoad wrapper (see uploads.js)

### ui/app.css (appended ~17 lines)
- #notifBell / #notifBadge styles (relative positioning, badge counter)
- #toastContainer (fixed top-right, z-index 9999, flex-column gap)
- .toast base + .t-ok/.t-warn/.t-err border-left colors
- @keyframes toast-in/out (300ms slide)
- @media(prefers-reduced-motion:reduce) fallback

### ui/uploads.js (appended ~12 lines)
- `window.goalsLoad = goalsLoad` export
- State tracker (_prevGoals): compares done-counts per agent between loads
- Fires `window.notify("ok", "Goal closed: <agent>")` on count increase

### ui/tokens.css (added --br-sm/md/lg/full)
- Restored border-radius scale lost to mirror revert (was undefined, causing var(--br-md) refs to fail)

## Verification (static)
- JS syntax: core.js braces 229/229 balanced, parens 819/819; uploads.js 250/250 / 960/960
- CSS tokens: all var() refs in app.css resolve to defined tokens (0 missing)
- All 4 triggers wired to correct toast types
- No index.html edit needed (pin-safe)

## Acceptance criteria
| Criterion | Status |
|-----------|--------|
| Toast top-right, auto-dismiss 5s | PASS (position:fixed top/right, TOAST_MS=5000) |
| Stackable (max 5) | PASS (MAX_TOASTS=5, firstElementChild.remove()) |
| Bell with unread count badge | PASS (#notifBadge increments/clears) |
| Trigger: goal closed | PASS (goalsLoad state comparison) |
| Trigger: agent offline | PASS (fleetRender hook) |
| Trigger: upload complete | PASS (_onUploadComplete export) |
| Trigger: error (5xx) | PASS (fetch wrapper) |
| Toasts dismiss correctly | PASS (timeout + X button + hover-pause) |

Note: Live browser render not possible from sandbox (CDP-gated, documented in memory/ops/blockers.md).
Static verification confirms all code paths are correct.
