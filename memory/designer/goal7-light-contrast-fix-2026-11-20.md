<!-- PROVENANCE agent=designer created=2026-11-20 trigger=goal7-light-mode-fix -->
# Goal 7 - Color Contrast + Accessibility: Light Mode Fix (2026-11-20)

## Problem
`contrast_audit.py` reported 30 failing pairs in LIGHT mode. Root cause: the [data-theme=light]
block did not override --ok, --warn, --err, --faint, --muted, or --warn-text, so they
inherited dark-mode values that are too light for white/near-white backgrounds.

## Fix Applied (ui/tokens.css, [data-theme=light] block)
| Token | Before | After | Min Ratio Now |
|-------|--------|-------|---------------|
| --ok | #1f9d5b | #187d48 | 4.56:1 |
| --warn | #c47a12 | #985f0e | 4.66:1 |
| --err | #d64545 | #c03e3e | 4.64:1 |
| --faint | #7a8699 | #646d7d | 4.61:1 |
| --muted | (inherited #8b93a7) | #666c7b | 4.64:1 |
| --warn-text | (inherited #e3b341) | #836725 | 4.72:1 |

## Verification
- `python memory/designer/contrast_audit.py` = DARK: ALL PASS, LIGHT: ALL PASS, 0 failures
- No dark-mode values changed (dark was already passing)
- All adjustments are hue-preserving darkening (no hue shift)

## Acceptance Criteria Status
| Criterion | Status |
|-----------|--------|
| Automated contrast check passes for all visible text | PASS (0 failures, both themes) |
| No new issues introduced | PASS (dark unchanged; light only darkened) |
| Dark mode also passes AA | PASS (was already passing, re-confirmed) |
