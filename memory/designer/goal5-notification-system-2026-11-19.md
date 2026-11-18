# Goal #5 - Notification System (2026-11-19)

## What was built
- **ui/notifications.js** (new file, 115 lines): self-contained IIFE module
  - Injects bell button into header + toast container into body on DOMContentLoaded
  - `window.notify(type, msg)` — creates a toast (top-right, auto-dismiss 5s, stackable max 4)
  - Bell click toggles dropdown panel showing last 30 notifications with timestamps
  - Unread count badge on bell (resets when panel opened)
  - Types: ok / warn / err / info (each with distinct left-border color from design tokens)
  - All styling uses CSS custom properties (--ok, --warn, --err, --acc, spacing tokens)
- **ui/app.css**: +30 lines of notification CSS (toast container, toast items, bell, badge, panel, animations)
- **ui/core.js** (+2 lines): dynamic script loader for notifications.js; global onerror now calls window.notify('err', ...)
- **ui/core.js fleetUpdate** (+6 lines): tracks previous host states in _fleetPrev; notifies 'warn' when a known host transitions to unknown
- **ui/uploads.js goalsLoad** (+5 lines): tracks previous done counts in _goalsPrev; notifies 'ok' when agent's done count increases
- **ui/uploads.js uploadFile** (modified 1 line): notifies 'ok' on upload success, 'err' on failure

## Triggers verified (code path)
| Trigger | Location | Type |
|---------|----------|------|
| Goal closed | uploads.js goalsLoad() comparison loop | ok |
| Agent offline | core.js fleetUpdate() state transition | warn |
| Upload complete | uploads.js uploadFile xhr.onload | ok |
| Upload failed | uploads.js uploadFile xhr.onload (else branch) | err |
| JS error | core.js window.onerror | err |

## Acceptance test status
- Toast: top-right ✅, auto-dismiss 5s ✅, stackable (cap 4) ✅
- Bell: unread badge ✅, dropdown panel ✅
- Colors match design tokens ✅ (uses var(--ok), var(--warn), var(--err), var(--acc))
- All 4 required triggers produce correct toast ✅ (code paths verified)

## Files modified
- ui/notifications.js (new)
- ui/app.css (+30 lines appended)
- ui/core.js (onerror enhanced + fleet offline detection + script loader)
- ui/uploads.js (goals comparison + upload notifications)