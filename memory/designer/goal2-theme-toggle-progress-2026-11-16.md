# Goal #2 Progress: Dark Mode + Theme Toggle (2026-11-16)

## What was done this round
- `ui/app.css`: Added `[data-theme="light"]` token block (10 color tokens: --bg, --panel, --panel2, --line, --text, --dim, --acc, --ok, --warn, --err, --focus, --faint) + `.theme-btn` styles
- `ui/core.js`: Added `initTheme()` IIFE that creates a toggle button dynamically in the header, reads/writes `localStorage["portal-theme"]`, falls back to `prefers-color-scheme`

## Verification
- CSS braces balanced (205/205)
- JS: initTheme present, localStorage key "portal-theme", data-theme attribute, prefers-color-scheme media query all confirmed
- No index.html edit needed (button created via DOM API)

## Remaining for full closure
- WCAG AA contrast check on both themes (need computed styles from live :8099)
- Screenshot pair (dark + light) as visual evidence
- Verify no contrast regressions in either mode
