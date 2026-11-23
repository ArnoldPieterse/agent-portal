# Cockpit Design-Token Completion (2026-11-24)

## What
Eliminated all 42 hardcoded hex colors in ui/cockpit.js, replacing them with CSS custom property references to the existing design token system (ui/tokens.css).

## Why
The cockpit was built by Builder with literal hex values (#2ea36b, #d4a017, #e5534b, #8a8f98, etc.) that bypassed the token layer. This meant:
- Light theme ([data-theme=light]) had no effect on cockpit colors
- Color changes required editing JS instead of tokens.css
- Inconsistent with the rest of the portal UI which uses var() references

## Mapping applied
| Old hex | Token | Role |
|---------|-------|------|
| #2ea36b | var(--ok) | success/green |
| #d4a017 | var(--warn) | warning/yellow |
| #e5534b | var(--err) | danger/red |
| #8a8f98 | var(--dim) | muted text |
| #aab2bf | var(--dim) | secondary text |
| #171b22 | var(--panel2) | card/panel bg |
| #2a2f38 | var(--line) | borders |
| #e8eaed | var(--text) | primary text |
| #101318 | var(--bg) | page bg |
| #232833 | var(--panel2) | bar track |
| #1d222b | var(--line) | subtle separator |
| #12151b | var(--panel) | input bg |
| #4a7ddb | var(--acc) | accent blue |

## SVG fix
Line 103 (health sparkline polyline): changed stroke= attribute to style="stroke:..." so CSS custom properties resolve correctly (var() does not work in SVG presentation attributes).

## Verification
- python regex scan: 42 hex before -> 0 after
- File size stable (16524 bytes, 257 lines)
- All var() references map to tokens defined in ui/tokens.css :root block

## Impact
- Cockpit now respects light/dark theme toggle
- Future palette changes = single edit in tokens.css
- Consistent with app.css, core.js, uploads.js which already use tokens

## Credit
Builder (cockpit frontend goals 2-8); Designer (token completion assist).
