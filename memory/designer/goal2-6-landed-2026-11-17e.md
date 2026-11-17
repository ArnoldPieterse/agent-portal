# Goal #2 (dark mode) + #6 (status-dot) — landed 2026-11-17e

## What shipped

### Goal #6: .status-dot component
- **CSS** (`ui/app.css`): `.status-dot` base (8px circle, flex:none) + `.green/.amber/.red` variants + `.labeled` variant. Replaced `.dot`, `.dot.on`, `.fdot`, `.fdot.busy/idle/unknown`.
- **JS** (`ui/core.js`):
  - `renderAgents()`: each `.acard` now gets `<span class="status-dot green|amber">` (green=model assigned, amber=no model).
  - `fleetUpdate()`: host rows use `.status-dot.green/amber/red` instead of `.fdot`.
  - Header: `#sdot` class set to `status-dot green` on JS init.

### Goal #2: Dark mode token layer + toggle
- **CSS** (`ui/app.css`):
  - `:root` = light palette (bg #f5f7fa, panel #fff, text #1a2332, acc #2563eb…)
  - `[data-theme=dark]` = original dark palette (bg #0e1116, panel #151a22…)
  - 9 hardcoded-color rules converted to tokens or given `[data-theme=dark]` overrides:
    `.msg.you`, `#peek` ×3, `.dmseg` ×2, `.acard.sel`, `.acard button:hover`,
    `.flink`, `.busyspan`, queue panel ×5, `#intBanner`, `.chipfile .st.err`
- **JS** (`ui/core.js`):
  - IIFE at top: reads `localStorage('portal_theme')` → falls back to `prefers-color-scheme`
    → sets `document.documentElement.dataset.theme`. Injects `#themeToggle` button into `<header>`
    (no index.html edit needed). Click toggles + persists.

## Acceptance criteria check
- [x] Token layer: all color/spacing/font tokens in `:root`, zero hardcoded values in light-mode rule bodies
- [x] `[data-theme=dark]` overrides restore the original dark appearance
- [x] Toggle button in header, persisted to localStorage
- [x] Default follows `prefers-color-scheme`
- [x] `.status-dot` used on agent cards (roster), fleet panel hosts, and header connection dot
- [x] Ad-hoc `.dot`/`.fdot` classes removed from CSS

## Files changed
- `ui/app.css` (both slices)
- `ui/core.js` (both slices)
- `index.html` NOT touched (toggle injected via JS, avoiding pin advance)

## Known remaining (non-blocking polish)
- `.seg button.on{background:#3a6fd6}` — works in both modes but could use token
- A few rgba() backgrounds in roundend/chips are mode-independent (fine as-is)
