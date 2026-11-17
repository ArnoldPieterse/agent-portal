# Goal 2 (Dark mode) — WCAG AA Contrast Audit
Date: 2026-11-17
Method: python script extracting all :root token pairs + hardcoded hex pairs from ui/app.css,
computing relative luminance per WCAG 2.1 formula, checking >=4.5:1 (normal text) and >=3:1 (large).

## Results
- 21 token pairs (7 fg x 3 bg): ALL PASS (min ratio 4.95:1 = --acc on --panel2)
- 8 hardcoded color pairs outside :root: ALL PASS (min 4.75:1 = #fff on #3a6fd6)
- Total failures: 0

## Key data
| Pair | Ratio | Status |
|------|-------|--------|
| --text on --bg | 16.08:1 | PASS |
| --dim on --panel2 | 6.52:1 | PASS |
| --faint on --panel2 | 5.45:1 | PASS |
| --acc on --panel2 | 4.95:1 | PASS (tightest) |
| #fff on #3a6fd6 | 4.75:1 | PASS (tightest hardcoded) |

## Remaining for full closure
- Screenshot pair (light + dark themes at :8099) — requires browser; not available in sandbox.
- Light theme token set does not yet exist (only dark tokens in :root). Contrast check above
  validates the current (dark) theme only. Light-mode contrast audit will run once --bg-light etc. are added.

## Verdict
Dark-theme WCAG AA contrast: **0 failures, PASS.** Script is re-runnable; save as
memory/designer/wcag_aa_contrast_check.py for regression gate (Goal 10).
