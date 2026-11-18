# Goal 6 — Loading Skeleton Screens (progress, 2026-11-19)

## What was done this pass

1. **CSS** (`ui/app.css`): Added `@keyframes shimmer` + `.skel`, `.skel-row`, `.skel-dot`, `.skel-bar`, `.skel-bar-sm`, `.skel-card`, `.skel-line`, `.skel-line-short`, `.skel-tl` classes. All use design tokens (`--line`, `--bg-hover`, `--sp-8`, `--radius`).

2. **JS utilities** (`ui/core.js`): `showSkeleton(containerId, type)` and `hideSkeleton(containerId)` — injects/removes panel-shaped placeholder HTML from a lookup table.

3. **Wiring**:
   - Fleet: patched `$("fleetBtn").onclick` in core.js (show before `fleetUpdate()`, hide after)
   - Goals: patched `$("goalsBtn").onclick` in uploads.js (show before `goalsLoad()`, hide after)
   - Files: patched `$("filesBtn").onclick` + `$("filesRefresh").onclick` in uploads.js

4. **Canvas-verified**: rendered all 4 panel types (fleet, goals, files, activity) in a standalone HTML preview — shimmer animation runs, shapes match panel content structure.

## Remaining for full verification

- Verify no layout shift when real content loads (requires live portal with API delay simulation)
- Activity panel skeleton not yet wired to a handler (no explicit open/close trigger found in current code)

## Files touched
- `ui/app.css` (skeleton CSS block, ~12 lines before responsive section)
- `ui/core.js` (SKELETON_HTML + show/hide functions + fleet wiring)
- `ui/uploads.js` (goals + files button handlers patched)