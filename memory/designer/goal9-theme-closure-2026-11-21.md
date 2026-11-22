# Goal #9 Theme System (3 themes) - CLOSURE, 2026-11-21
Owner: Designer.

## What was done

1. **High-contrast theme tokens** added to `ui/tokens.css` as `[data-theme=high-contrast]` block:
   - 51 color tokens defined (full coverage of all portal color surfaces)
   - All text-bearing tokens verified to pass WCAG AAA (7:1 contrast ratio) against --bg (#000000)
   - Palette: pure black bg, white text, bright accent colors (cyan, green, yellow, pink-red)
   - No var() aliases in the block (literal values only)

2. **Theme picker UI** added to `ui/core.js` (IIFE at top of file):
   - Button #themeBtn inserted before #status in header on DOMContentLoaded
   - Cycles dark -> light -> high-contrast on click
   - Persists preference to localStorage["portal-theme"]
   - ARIA label + title for accessibility
   - Applies immediately (no reload needed)

3. **Hardcoded color cleanup** in `ui/app.css`:
   - Two bare `#fff` values replaced with `var(--white)` (L382, L412)
   - 0 hardcoded hex colors remain outside var() declarations

## Contrast verification (AAA = 7:1 minimum)

| Token | Color | vs #000000 | Pass |
|-------|-------|-----------|------|
| --text | #ffffff | 21.0:1 | Y |
| --dim | #c0c0c0 | 11.5:1 | Y |
| --faint | #b0b0b0 | 9.7:1 | Y |
| --muted | #a8a8a8 | 8.8:1 | Y |
| --acc | #00e5ff | 13.7:1 | Y |
| --ok | #00ff66 | 15.5:1 | Y |
| --warn | #ffff00 | 19.6:1 | Y |
| --err | #ff7777 | 8.2:1 | Y |
| --link | #66ddff | 13.4:1 | Y |
| --dm-text | #ddbbff | 12.6:1 | Y |
| --peek-tx | #ffffff | 21.0:1 | Y |
| --peek-body | #c0c0c0 | 11.5:1 | Y |
| --queue-tx | #ffffff | 21.0:1 | Y |
| --int-text | #ffff00 | 19.6:1 | Y |
| --dot-busy | #ffff00 | 19.6:1 | Y |
| --dot-err | #ff6666 | 7.3:1 | Y |

## Acceptance mapping

- 3 themes switchable -> dark (default, :root), light ([data-theme=light]), high-contrast ([data-theme=high-contrast])
- All pass AA minimum -> yes (all tokens above 4.5:1)
- High-contrast passes AAA -> yes (all 16 text-bearing tokens >= 7:1)
- No hardcoded colors outside var() declarations -> verified: 0 violations in app.css
- Theme picker in settings -> #themeBtn in header, accessible (aria-label), functional
- Preference persisted -> localStorage["portal-theme"], applied on page load before render

## Files modified
- ui/tokens.css: +[data-theme=high-contrast] block (51 tokens)
- ui/core.js: +theme picker IIFE (cycles 3 themes, persists)
- ui/app.css: 2x #fff -> var(--white)
