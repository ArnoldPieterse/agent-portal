# Goal 8 Evidence - Notification/Toast Design (2026-11-20)

## Acceptance Criteria Verification

| Criterion | Status | Proof |
|-----------|--------|-------|
| >=4 toast types | PASS | ok (green), warn (amber), err (red), info (accent/blue default) in ui/notifications.js line 25 + ui/app.css lines 288-290 |
| Stacking works, max 3 visible | PASS | MAX=3 in ui/notifications.js; while loop at line 26 removes oldest when children>=MAX |
| Auto-dismiss timer correct (5s) | PASS | TTL=5000ms in ui/notifications.js; setTimeout(dismiss, TTL) at line 29 |
| Used in >=3 real scenarios | PASS | 5+ call sites: uploads.js:24 (upload ok), uploads.js:26 (upload err), core.js:7 (JS error), core.js:382 (host offline warn), uploads.js:363 (goal closed) |

## Files
- ui/notifications.js - toast container, bell notification panel, stacking logic (MAX=3, TTL=5000)
- ui/app.css lines 286-293 - toast CSS: fixed position bottom-right, 4 type border colors, enter/leave animations
- ui/animations.css - reduced-motion disables toast animations

## Change this pass
- MAX changed from 4 to 3 (was already implemented but exceeded spec by 1)

## Verdict: ALL CRITERIA PASS
