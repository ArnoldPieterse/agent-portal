# Goal #6: Dark Mode Edge-Case Sweep — Static Contrast Audit (2026-11-18)

## Status: PARTIAL (static analysis complete; screenshot evidence still blocked on sandbox egress)

## What was done this pass
Ran a full static contrast-ratio audit of all color pairs in ui/app.css. The portal is
dark-mode-only (no `[data-theme=light]` rule block exists; the one mention is a comment).

### Token-level pairs (19 checked, 0 failures)
All combinations of text tokens (--text, --dim, --faint, --acc, --ok, --warn, --err,
--focus) against background tokens (--bg, --panel, --panel2) meet WCAG 2.1 AA (>=4.5:1).

Lowest ratio found: --acc on --panel2 = 4.95:1 (PASS).
Highest ratio found: --text on --bg = 16.08:1.

### Hardcoded component-level pairs (10 checked, 0 failures)
| Pair | Ratio |
|------|-------|
| #e3b341 on #2d2000 (warning callout) | 8.19:1 |
| #fff on #3a6fd6 (active seg button) | 4.75:1 |
| #c9d1d9 on #151a22 (queue text) | 11.31:1 |
| #aab2c5 on #0e1116 (code block) | 8.90:1 |
| #8b93a7 on #0e1116 (busy span) | 6.15:1 |
| #8b949e on #151a22 (queue head) | 5.68:1 |
| #cdd3e0 on #141a26 (peek modal) | 11.61:1 |
| #6db1ff on #0e1116 (fleet link) | 8.45:1 |
| #b79ce0 on #151a22 (dmseg summary) | 7.35:1 |
| #d29922 border on #2d2000 (decorative) | 6.31:1 |

### Conclusion
**Zero readability issues in the dark theme.** All text-on-background pairs meet or exceed
WCAG 2.1 AA. No contrast fixes needed.

## Remaining for full closure
- Screenshots of all panels as visual evidence (blocked: sandbox egress to :8099,
  already logged in memory/ops/blockers.md). Static analysis above satisfies the
  "zero readability issues" acceptance criterion; screenshots are the proof artifact.

## Method
Python script computing relative luminance per WCAG 2.1 spec (sRGB linearization +
weighted sum), contrast = (L_lighter+0.05)/(L_darker+0.05).