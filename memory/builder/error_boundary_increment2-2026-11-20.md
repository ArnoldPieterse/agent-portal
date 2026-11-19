# Error Boundary System — Increment 2 (2026-11-20)

## What was done
The 2026-11-18 increment was reverted by mirror (showPanelError/safePanel absent from core.js). Re-implemented cleanly:

**ui/core.js** (+14 lines after line 19):
- `showPanelError(el, msg, retryFn)` — replaces element innerHTML with a styled `.panel-error` card: icon + truncated message (200 chars) + optional Retry button. Retry clears the card and re-invokes the panel's update function.
- Wired into 3 main panel catch blocks:
  - `actUpdate` → error card in `#actBody`, retry calls `actUpdate()`
  - `fleetUpdate` → error card in `#fleetBody`, retry calls `fleetUpdate()`
  - `opsLoad` (git section) → error card in `#gitStatus`, retry calls `opsLoad()`

**ui/app.css** (+6 lines before reduced-motion block):
- `.panel-error` — flex column, dashed border, centered, uses existing design tokens (--dim, --line, --sel-bg, --acc)
- `.pe-icon`, `.pe-msg`, `.pe-retry` sub-elements

## Verification (static)
- Braces: 276/276 balanced ✓
- Parens: 973/973 balanced ✓
- Helper defined at line ~21, first use in actUpdate at line ~340 — definition precedes all uses ✓
- `showPanelError` present in core.js ✓
- All 3 catch blocks wired ✓
- CSS `.panel-error` and `.pe-retry` present in app.css ✓

## Remaining for full closure
- Live browser test: kill portal → open a panel → verify error card appears → restart portal → click Retry → panel restores (requires live environment with portal running)
- `opsTiles` catch block still uses raw textContent (low priority — tiles are small, the main opsBody is covered by gitStatus boundary)

## Files modified
- ui/core.js (+14 lines: helper + 3 catch-block upgrades)
- ui/app.css (+6 lines: .panel-error styles)