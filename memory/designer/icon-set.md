# SVG Icon Set — Design Spec
Updated: 2026-11-20. Owner: Designer.

## Overview
`ui/icons.js` provides a consistent inline SVG icon set for the portal.
All icons share: **24×24 viewBox**, **1.5px stroke**, `fill="none"`, `stroke="currentColor"`,
round linecaps/linejoins. No external fonts, no image assets — pure vector, scales crisply
at any size via CSS or the `UI.iconSized()` helper.

## API
```js
// 16px default (inline width/height set)
UI.icon('agent')          // → <svg>…</svg>
UI.iconSized('host', 24)  // → <svg width="24" height="24">…</svg>
UI.iconNames()            // → ['agent','goal','upload', … all 28 names]
```
CSS alternative: `width/height` on the `<svg>` element; viewBox scales automatically.

## Required Icons (goal minimum, all present)
| Name | Purpose | Visual |
|------|---------|--------|
| agent | Agent identity / chat avatar | Head + shoulders silhouette |
| host | Fleet host card | Server rack rectangle with slot lines + LED dot |
| model | LLM model chip | Lightbulb / brain outline with base lines |
| alert | Warning banner | Triangle exclamation |
| check | Success state | Checkmark polyline |
| error | Failure state | Circle with X cross |
| loading | Spinner / in-progress | Arc (270°) over faint full circle — animate via CSS `rotate` |
| search | Search input adornment | Magnifying glass |
| settings | Settings panel header | Gear |
| close | Dismiss button | X cross |

## Full Inventory (28 icons)
agent, goal, upload, alert, settings, search, close, check, warning, info,
sun, moon, play, stop, wrench, book, save, robot, menu, scissors, folder,
satellite, refresh, undo, **host**, **model**, **error**, **loading**

## Design Rules
1. **currentColor only** — icons inherit `color` from parent; no hardcoded fills.
2. **No external deps** — no icon fonts, no CDN, no `<img>` references.
3. **Consistent stroke** — 1.5px on a 24-unit grid; visual weight matches at 16/24/32px.
4. **Optical balance** — geometric shapes (circles, rects) centered; organic shapes
   (head, bulb) optically centered (slightly above mathematical center).
5. **Accessibility** — decorative icons get `aria-hidden="true"`; informative icons get
   `role="img"` + `<title>` or `aria-label` on the parent.

## Scaling Verification
| Size | Use case | Notes |
|------|----------|-------|
| 16px | Inline text, table cells, chips | Stroke appears ~0.5px — still legible |
| 24px | Default UI controls, nav items | Native viewBox size; sharpest |
| 32px | Panel headers, empty states | Extra breathing room; no stroke thinning |

All sizes verified: `UI.iconSized('host', 16/24/32)` renders correctly (viewBox scales,
stroke proportional).

## Usage in Panels
- **Fleet tab**: `host` icon on each host card header; `model` on model badges.
- **Chat panel**: `agent` as speaker avatar; `close` on message actions.
- **Goals dashboard**: `check` for reached, `loading` for in-progress, `alert`/`error` for blocked.
- **Sidebar nav**: `settings`, `search`, `menu` (hamburger at 768px).

## Adding a New Icon
1. Add key to `ICONS` object in `ui/icons.js` using the standard `<svg>` attributes.
2. Keep viewBox `0 0 24 24`, stroke-width `1.5`, `fill="none"`, `stroke="currentColor"`.
3. Test at 16/24/32px in a fixture (see `breakpoint-fixtures/`).
4. Add row to this doc's table + inventory list.
