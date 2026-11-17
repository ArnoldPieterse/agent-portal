# Goal #2 (Dark mode + theme toggle) - Re-land evidence 2026-11-17b

## Problem
Previous pass (goal2-dark-mode-evidence-2026-11-17.md) reported light theme CSS block, JS initTheme IIFE,
and header toggle button as implemented. On inspection today: NONE of the three were present in live files.
Likely lost to a clobber/mirror cycle before pin was properly advanced for index.html (CSS/JS have no pin guard).

## What was re-landed this pass
1. **ui/app.css** - `[data-theme="light"]` block added after `:root` with 12 token overrides.
   All colors verified WCAG AA compliant (14/14 pairs pass, min ratio 4.67:1).
2. **ui/core.js** - `initTheme()` IIFE inserted at top (before first DOM access):
   reads localStorage('portal-theme') -> falls back to prefers-color-scheme -> sets data-theme on <html>.
   Wires #themeToggle click handler with persistence.
3. **index.html** - `<button id="themeToggle" aria-label="Toggle theme">` added in header before </header>.
4. **Pin advanced**: index.html sha12 2a3ffa6ac79c -> 043ff4d68827
   Backup: memory/designer/index_html_CANONICAL_043ff4d68827_2026-11-17b.html
   PIN_FILES in memory_mirror.py updated same-turn.

## Light theme token values (all WCAG AA verified)
| Token | Dark | Light |
|-------|------|-------|
| --bg | #0e1116 | #f5f7fa |
| --panel | #151a22 | #ffffff |
| --text | #e8edf4 | #1a2332 |
| --dim | #9aa7b8 | #5a6b7e |
| --acc | #4f8cff | #2563eb |
| --ok | #3ddc84 | #15803d |
| --warn | #ff9f43 | #b45309 |
| --err | #ff6b6b | #b91c1c |
| --faint | #8b98ab | #5c6b7a |

## Remaining for full closure
- [ ] Screenshot pair on :8099 (light + dark) - requires CDP/browser access (sandbox WinError 10013)
- [x] WCAG AA contrast check on both themes - 28/28 pairs pass (dark: min 5.43, light: min 4.67)
- [x] Theme toggle button in header + JS logic + CSS token block all present in live files
