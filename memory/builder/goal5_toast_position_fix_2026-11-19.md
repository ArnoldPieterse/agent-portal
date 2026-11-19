# Builder assist: Designer Goal #5 Notification System - toast position fix (2026-11-19)

## What was done
Fixed `.toast-container` CSS from `bottom:var(--sp-16)` to `top:var(--sp-16)` in ui/app.css (line 287).
Spec requires "top-right" toast placement; implementation had it at bottom-right.

## Full Goal #5 status assessment
All code for Goal #5 is present and wired:
- **JS**: ui/notifications.js exists, loaded via <script> tag in index.html
- **CSS**: 25 lines of toast/notif styles in ui/app.css (tokens-compliant)
- **Triggers** (all 4 wired):
  1. Goal closed -> uploads.js: notify("ok","Goal closed on ...")
  2. Agent offline -> core.js: notify("warn","Agent host ... is offline")
  3. Upload complete -> uploads.js: notify("ok","Upload complete: ...")
  4. Error -> core.js (onerror) + uploads.js (xhr.onerror): notify("err",...)

## Remaining for acceptance
- Browser rendering test (same sandbox blocker as #2/#6/#10)
- Bell badge update verification in browser
- Toast dismiss animation visual check

## File changed
- ui/app.css line 287: bottom->top (1 word)
