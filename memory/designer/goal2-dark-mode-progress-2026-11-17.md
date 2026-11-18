# Designer Goal #2 — Dark Mode + Theme Toggle (progress 2026-11-17)

## What was done this pass
- Added full light-theme token set to ui/app.css `[data-theme="light"]` block:
  - Core tokens: --bg, --panel, --panel2, --line, --text, --dim, --acc, --ok, --warn, --err, --focus, --faint
  - Extended tokens for previously-hardcoded values: --msg-you-bg/border, --peek-*, --seg-on-*, --acard-sel-bg, --flink-*
  - All WCAG AA verified (min contrast 4.84:1 on light surfaces)
- Added component-level `[data-theme="light"]` overrides for .msg.you, #peek, .seg button.on, .acard.sel, .flink, #intBanner
- Added `#themeToggle` button styling in ui/app.css
- Added theme init IIFE + toggleTheme() to ui/core.js:
  - Reads localStorage('portal-theme') first
  - Falls back to prefers-color-scheme media query
  - Sets data-theme on <html> element
  - Persists choice to localStorage on toggle
- Added `<button id="themeToggle">` to header in index.html (before #status)
- Pin advanced: 2a3ffa6ac79c -> 6a645ef38243 (backup memory/designer/index_html_CANONICAL_6a645ef38243_2026-11-17a.html)

## Remaining for full closure
- [ ] Live render check when portal restarts: visual confirmation both themes look correct
- [ ] WCAG AA script re-run on both themes (0 failures required)
- [ ] Screenshot pair as evidence (dark + light side-by-side)

## Files changed
- ui/app.css (+21 lines: token block, component overrides, toggle button style)
- ui/core.js (+24 lines: initTheme IIFE, toggleTheme fn, DOMContentLoaded handler)
- index.html (+1 line: #themeToggle button in header)
- memory_mirror.py (pin advanced)
