# Designer Goal #1 — Design Token Gap Audit (concrete step, 2026-11-17)

## Scope
Grep ui/app.css for hard-coded color values outside the :root token block.

## Finding
**36 hex color values** found in 28 unique colors used OUTSIDE :root.
These are not using var(--token) and violate the design-token discipline.

## Offenders (by frequency)
- `#fff` — 3 occurrence(s), properties: color
- `#8b949e` — 3 occurrence(s), properties: animation, color
- `#2a3342` — 2 occurrence(s), properties: background
- `#8b93a7` — 2 occurrence(s), properties: color
- `#9ccaff` — 2 occurrence(s), properties: border-bottom, color
- `#2c3548` — 2 occurrence(s), properties: border, border-bottom
- `#20304d` — 1 occurrence(s), properties: background
- `#3a6fd6` — 1 occurrence(s), properties: font-size
- `#243b63` — 1 occurrence(s), properties: background
- `#33507f` — 1 occurrence(s), properties: border-color
- `#3ddc84` — 1 occurrence(s), properties: margin-top
- `#4a3f6b` — 1 occurrence(s), properties: border
- `#b79ce0` — 1 occurrence(s), properties: color
- `#ff6b6b` — 1 occurrence(s), properties: flex
- `#6db1ff` — 1 occurrence(s), properties: animation
- `#141a26` — 1 occurrence(s), properties: background
- `#cdd3e0` — 1 occurrence(s), properties: color
- `#aab2c5` — 1 occurrence(s), properties: color
- `#888` — 1 occurrence(s), properties: background
- `#ffb454` — 1 occurrence(s), properties: background
- `#e05252` — 1 occurrence(s), properties: background
- `#0d1117` — 1 occurrence(s), properties: background
- `#30363d` — 1 occurrence(s), properties: border
- `#58a6ff` — 1 occurrence(s), properties: border-top-color
- `#c9d1d9` — 1 occurrence(s), properties: color
- `#d29922` — 1 occurrence(s), properties: border
- `#2d2000` — 1 occurrence(s), properties: background
- `#e3b341` — 1 occurrence(s), properties: color

## Next step (not yet done)
- Assign token names to each unique color (group by semantic role)
- Add new tokens to :root in app.css
- Replace all hard-coded values with var(--token)
- Re-run grep to confirm 0 hits outside :root

Status: **IN PROGRESS** — audit complete, remediation pending.
