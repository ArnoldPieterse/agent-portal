# Goal #2 (Dark mode + theme toggle) - Re-land 2026-11-17d

## Status: CSS + JS in place; pending screenshot pair for full closure

### What was done this pass
1. **ui/app.css** - `[data-theme="light"]` block inserted after :root close-brace with 12 core token overrides.
   Values chosen to pass WCAG AA (>=4.5:1) on all 10 primary fg/bg pairs:
   | Token | Value | Contrast vs bg |
   |-------|-------|---------------|
   | --text | #1e293b | 13.98:1 |
   | --dim | #475569 | 7.24:1 |
   | --acc | #2563eb | 4.94:1 |
   | --ok | #15803d | 4.79:1 |
   | --warn | #b45309 | 4.80:1 |
   | --err | #dc2626 | 4.62:1 |
   | --faint | #64748b | 4.55:1 |

2. **ui/core.js** - `initTheme()` IIFE at file top (before first DOM access):
   - reads localStorage('portal-theme') -> falls back to prefers-color-scheme -> sets data-theme on <html>
   - Creates <button id="themeToggle"> injected into header before #status
   - Persists choice; tracks system pref changes when user has not explicitly chosen
   - Sun/moon unicode label (☾ dark / ☽ light)

### Remaining for full closure
- [ ] Screenshot pair (dark + light) on :8099 - requires portal up + CDP/browser access
- [x] WCAG AA contrast check both themes: 10/10 PASS, 0 failures
- [x] Theme tokens in ui/app.css ([data-theme="light"] block)
- [x] JS toggle with localStorage persistence in ui/core.js

### Anti-clobber note (3rd clobber cycle confirmed)
ui/app.css and ui/core.js are NOT pin-guarded. Git not available in sandbox.
Action needed: commit from White session after next mirror cycle, OR add these files to PIN_FILES.
