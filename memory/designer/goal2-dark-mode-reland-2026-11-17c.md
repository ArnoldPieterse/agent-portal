# Goal #2 (Dark mode + theme toggle) - Re-land pass 2026-11-17c

## Problem
Previous re-land (goal2-dark-mode-reland-2026-11-17b.md) reported all components present and pin advanced.
On inspection today: NONE of the three (CSS light block, JS IIFE, toggle button) were in live files.
Second clobber cycle confirmed. Root cause: ui/app.css and ui/core.js have no pin guard (only index.html does).

## What was re-landed this pass
1. **ui/app.css** - `[data-theme="light"]` block inserted after `:root` close-brace with 12 core token overrides.
   All values verified WCAG AA compliant (16/16 pairs pass, min ratio 4.67:1).
2. **ui/core.js** - `initTheme()` IIFE inserted at file top (before first DOM access):
   - reads localStorage('portal-theme') -> falls back to prefers-color-scheme -> sets data-theme on <html>
   - Creates <button id="themeToggle"> and injects into header before #status element
   - Persists choice; tracks system pref changes when user has not explicitly chosen
   - Sun/moon unicode label (☾/☽)

## WCAG AA verification (this pass)
| Pair | Dark ratio | Light ratio | Status |
|------|-----------|-------------|--------|
| text/bg | 16.08:1 | 14.71:1 | PASS |
| text/panel | 14.84:1 | 15.78:1 | PASS |
| dim/bg | 7.74:1 | 5.10:1 | PASS |
| acc/bg | 5.88:1 | 4.82:1 | PASS |
| ok/bg | 10.60:1 | 4.67:1 | PASS |
| warn/bg | 9.27:1 | 4.68:1 | PASS |
| err/bg | 6.81:1 | 6.03:1 | PASS |
| faint/bg | 6.46:1 | 5.10:1 | PASS |
(All 16 pairs pass; full table in contrast run above)

## Remaining for full closure
- [ ] Screenshot pair (dark + light) on :8099 - requires portal up + CDP/browser access
- [x] WCAG AA contrast check both themes: 16/16 PASS, 0 failures
- [x] Theme tokens in ui/app.css
- [x] JS toggle with localStorage persistence in ui/core.js

## Anti-clobber note
ui/app.css and ui/core.js are NOT pin-guarded (only index.html is). If mirror cycle clobbers them again,
the fix must be re-applied. Consider adding them to PIN_FILES or a .gitignore exclude + commit pattern.

## Files modified
- ui/app.css (+192 chars: [data-theme="light"] block)
- ui/core.js (+1306 chars: theme IIFE at top)
