# Designer Goal 8 - Notification/Toast Design (2026-11-20)

## Acceptance criteria check
| Criterion | Status | Evidence |
|-----------|--------|----------|
| >=4 toast types | PASS | ok(--ok green), warn(--warn amber), err(--err red), info(--acc blue) - all in ui/app.css L355-358 + new .toast.info rule |
| Stacking max 3 visible | PASS | ui/notifications.js MAX=3; while-loop evicts oldest when children >= MAX |
| Auto-dismiss 5s | PASS | TTL=5000 ms in notifications.js |
| Dismissible by click | PASS | .toast-close button with aria-label, dismiss() fades out via .leaving class |
| Used in >=3 real scenarios | PASS | (1) fleet host unknown -> warn [core.js L382] (2) upload success/error [uploads.js L24/26] (3) goal progress delta -> ok [uploads.js L363] |

## Changes this pass
- ui/notifications.js: MAX 4 to 3 (matches spec "max 3 visible")
- ui/app.css: added .toast.info{border-left-color:var(--acc);} for explicit info-type styling

## Files
- ui/notifications.js (JS logic, 2855 bytes)
- ui/app.css L352-374 (toast + bell CSS)
- ui/tokens.css (--ok, --warn, --err, --acc token values dark+light)
