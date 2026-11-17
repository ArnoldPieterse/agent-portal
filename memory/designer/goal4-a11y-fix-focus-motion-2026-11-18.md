# Goal #4 WCAG 2.1 AA — Focus + Motion Fix (2026-11-18)

## What was done
Added two blocks to `ui/app.css` (end of file, lines 270-273):

1. **Universal `:focus-visible` rule** (line 271): Covers `button`, `input`, `select`, `textarea`, `a`, `[tabindex]`, `summary` — all get `2px solid var(--focus)` outline with 2px offset. This supersedes the narrower selectors on lines 141-143 which only covered ops/modeBar buttons.

2. **`prefers-reduced-motion` media query** (line 273): Disables all transitions/animations when user has reduced motion preference set. Uses `!important` to override any component-level animation durations.

## WCAG criteria addressed
| Criterion | Before | After |
|-----------|--------|-------|
| SC 2.4.7 Focus Visible | PARTIAL (only #opsPanel + #modeBar buttons had rings) | PASS (all interactive elements covered) |
| SC 2.3.3 Animation from Software | FAIL (no reduced-motion block) | PASS (block present, disables all motion) |

## Why the prior evidence was stale
The consolidated audit (`wcag-aa-audit-consolidated-2026-11-18.md`) recorded both fixes as applied, but they were lost — likely reverted by a mirror/pin cycle that restored an older `app.css` snapshot. The `:focus-visible` narrow selectors (lines 141-143) survived because they were in the middle of the file; the appended blocks at EOF did not.

## Remaining for full goal #4 closure
- [ ] Skip-to-content link (`<a class="skip" href="#main">`) — requires index.html pin advance
- [ ] Panel `<section>` conversion with `role="region"` + `aria-label` — requires index.html pin advance
- [ ] Final audit pass confirming zero remaining violations

## Files touched
- `ui/app.css` (2 lines appended at EOF; sha change expected)

## Verification command
```
grep -c 'focus-visible' ui/app.css   # expect >= 2 (the narrow + universal rules)
grep -c 'prefers-reduced-motion' ui/app.css  # expect 1
```