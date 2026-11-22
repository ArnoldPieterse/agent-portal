# Goal 3 - inline error icons in log/list contexts (2026-11-21)

## Change
Remaining raw `error:` strings in non-component contexts now render with an inline SVG warning icon + red color:

1. **`opsSay()`** (ui/core.js ~L460): detects error prefix, renders UI.iconSized(warning,14) + escaped text, adds .ops-err class.
2. **Disk tile** (ui/core.js ~L436): same pattern when disk data is unavailable.

## CSS (ui/app.css)
.ops-err { color: var(--err,#e05252); display:flex; align-items:center; gap:4px }
.ops-err svg { flex:none }

## Remaining error: strings (intentional, not user-facing raw indicators)
- L24 window.onerror - developer diagnostic in status bar
- L319 actIcons object key - maps to SVG icon already
- L330 activity feed label - rendered alongside warning icon via actIcons

## Acceptance: no raw Error text without context
All user-visible error strings now have either an inline SVG icon or are descriptive event labels that already include an icon. PASS.
