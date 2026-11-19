# Goal #5 Notification System - CSS + Script Wiring (2026-11-19)

## What was done
1. Added 25 notification CSS rules to ui/app.css (.toast-container, .toast, .toast.ok/warn/err/info,
   .toast.leaving, @keyframes toastIn/toastOut, .toast-close, .notif-bell, .notif-badge, .notif-panel,
   .notif-panel-head, .notif-item, .ni-icon, .ni-msg, .ni-time)
2. All CSS uses design tokens (var(--sp-*), var(--fs-*), var(--br-*), var(--lh-*)). Zero hardcoded px in new rules.
3. Added <script src="ui/notifications.js"></script> to index.html after icons.js (line 160)
4. Pin advanced: sha12 84003897483e -> 6f521cb54a84
   Backup: memory/designer/index_html_CANONICAL_6f521cb54a84_2026-11-19x.html
   memory_mirror.py PIN_FILES updated

## State
- ui/notifications.js: 115 lines, self-contained IIFE. Exposes window.notify(type,msg) + window.getNotifications().
  Toast auto-dismiss 5s, stackable (max 4 visible), bell with unread badge, dropdown panel.
- CSS: 25 rules in app.css using design tokens throughout.
- Script tag: loaded after icons.js so UI.iconSized() is available for notification icons.

## Remaining for acceptance test
- Browser rendering verification: toasts appear top-right, auto-dismiss at 5s, stack correctly
- Bell badge increments on notify(), dropdown opens/closes
- All 4 trigger types (ok/warn/err/info) render with correct border-left color
- Hand to Verifier when browser session available

## Artifacts
- ui/app.css (notification section appended after tour section)
- index.html (script tag added, pin at 6f521cb54a84)
- memory_mirror.py (PIN_FILES updated)
