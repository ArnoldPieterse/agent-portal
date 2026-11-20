# Icon Usage Progress - 2026-11-20 (pass N)

## Changes Made
- ui/notifications.js: Added type-specific icon to each toast (success/warning/alert/info by kind)
- ui/fleet_health.js: Added status icon per host badge (success/warning/alert by tone)
- ui/app.css: Added .toast-icon and .fh-status-icon CSS rules

## Icon Panel Count After This Pass
| Icon | Panels | Status |
|------|--------|--------|
| warning | 3 (activity feed, fleet health, notifications) | MEETS BAR |
| alert | 3 (activity feed, fleet health, notifications) | MEETS BAR |
| wrench | 3 (tool chips, activity feed, opsHead) | MEETS BAR |
| success | 2 (fleet health, notifications) | needs 1 more |
| info | 2 (empty states, notifications) | needs 1 more |
| close | 2 (roster delete, toast dismiss) | needs 1 more |

## Remaining Gap
17+ icons still need >=3 panel contexts each. Next step: integrate chevron/refresh/search/status icons into goals dashboard + fleet topology panels.
