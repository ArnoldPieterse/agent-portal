# Light Theme WCAG AA Contrast Audit - 2026-11-23 (Designer)

## Finding
Light theme has **6 tokens below the 4.5:1 AA threshold** for normal text (<18pt).
Dark theme passes all pairs comfortably (lowest: --faint at 5.97:1 on panel).

## Failing pairs (light, against --bg #f4f6fa)
| Token | Current | Ratio | Target | Suggested Fix |
|-------|---------|-------|--------|---------------|
| --faint | #7a8699 | 3.41:1 | 4.5:1 | **#667080** (4.63:1) |
| --acc | #2f6fe0 | 4.34:1 | 4.5:1 | **#2e6cdb** (4.53:1) |
| --ok | #1f9d5b | 3.22:1 | 4.5:1 | **#19804a** (4.59:1) |
| --warn | #c47a12 | 3.16:1 | 4.5:1 | **#9c610e** (4.70:1) |
| --err | #d64545 | 4.05:1 | 4.5:1 | **#c94040** (4.52:1) |
| --muted | #64748b | 4.40:1 | 4.5:1 | **#627188** (4.58:1) |

## Impact
- `--faint` is used for placeholder text and disabled states - fails AA at all common sizes
- `--ok` / `--warn` are status colors on VRAM bars and agent cards - small text labels fail
- `--acc` is the primary action color (buttons, links) - just 0.16:1 short
- `--muted` is secondary metadata text - 0.10:1 short

## Fix
Edit the `[data-theme=light]` block in `ui/tokens.css`, replacing the 6 hex values above.
No structural changes needed; dark theme unaffected.

## Verification method
Computed per WCAG 2.1 relative luminance formula (sRGB linearization + weighted sum).
Cross-checked: all "PASS" pairs in dark theme are at/above 5.9:1 - no risk of regression from this fix.

## Status
- Audit complete, fixes identified
- Application to tokens.css is a one-line-per-token edit for Builder (or I can do it directly)
- After applying, re-run Playwright B-series theme tests to confirm no visual breakage
