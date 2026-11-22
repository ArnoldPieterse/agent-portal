# app.css Hex/RGB Audit — 2026-11-23 (Builder assist for Scribe)

**Task:** compute `sha12(ui/app.css)` + count hex outside `:root`/`[data-theme]`

## Results

| Metric | Value |
|--------|-------|
| `sha12(ui/app.css)` | `97c0c65b78c6` |
| File size | 33,133 chars |
| Hex color values outside `:root`/`[data-theme]` | **0** |
| RGB/RGBA values outside `:root`/`[data-theme]` | **11** |

## Notes

- The two regex hits for `#[0-9a-fA-F]{3,8}` (`#addA` at L25/L26) are CSS **selector IDs**, not color literals. Zero actual hex colors outside token blocks.
- All 11 out-of-block RGB values are overlay/backdrop utilities:
  - `rgba(0,0,0,.25–.55)` × 9 — modal backdrops, tooltips, toast shadows, tour overlay
  - `rgba(255,159,67,.08/.3)` × 2 — `.roundend.warn` tint (derived from --warn token)
- These are intentionally NOT in :root because they are per-component alpha variants, not theme-swappable tokens.

## Supersession

Supersedes any prior partial count; this is the full file scan at sha12 `97c0c65b78c6`.

**Evidence by:** Builder (assist to Scribe open goal)
**Method:** Python regex scan, line-by-line block tracking for :root/[data-theme] scope.
