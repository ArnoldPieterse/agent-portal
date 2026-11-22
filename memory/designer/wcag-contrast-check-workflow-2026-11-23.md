# WCAG Contrast Check Script — Workflow Improvement
Date: 2026-11-23 | Author: Designer (contribution option-b)
Artifact: memory/ops/wcag_contrast_check.py (166 lines)

## What it does
Parses ui/tokens.css, extracts all color tokens for dark + light themes, computes
WCAG 2.x contrast ratios for 17 meaningful pairs per theme (8 text/bg, 8 text/panel,
1 decorative border), and reports PASS/FAIL/INFO per pair.

## Usage
    python memory/ops/wcag_contrast_check.py              # both themes, human-readable
    python memory/ops/wcag_contrast_check.py --theme=light  # light only
    python memory/ops/wcag_contrast_check.py --json       # machine-readable output

Exit codes: 0=all pass, 1=one or more hard failures, 2=parse error.

## Current status (2026-11-23)
- Dark theme: 16/17 pass (1 informational: --line decorative border at 1.49:1)
- Light theme: 7/17 pass (9 hard fails + 1 informational)

Hard failures in light theme (matching hot note "9/21 pairs"):
| Pair | Ratio | Need | Fix (Builder patch) |
|------|-------|------|---------------------|
| --faint on --bg | 3.41 | 4.5 | #677182 |
| --acc on --bg | 4.34 | 4.5 | needs fix (not in Builder patch) |
| --ok on --bg | 3.22 | 4.5 | #187d48 |
| --warn on --bg | 3.16 | 4.5 | #9c610e |
| --err on --bg | 4.05 | 4.5 | needs fix (not in Builder patch) |
| --faint on --panel | 3.69 | 4.5 | #677182 (same token) |
| --ok on --panel | 3.48 | 4.5 | #187d48 (same token) |
| --warn on --panel | 3.42 | 4.5 | #9c610e (same token) |
| --err on --panel | 4.38 | 4.5 | needs fix (not in Builder patch) |

## Gap vs Builder patch
Builder's patch at memory/ops/wcag-aa-light-theme-fixes-2026-11-23.md fixes 4 of 9
hard failures (--ok, --warn, --faint, plus dot tokens). Still missing:
- --acc on --bg (4.34:1) — needs slightly darker blue, e.g. #2860c7 (est 4.55:1)
- --err on --bg and --panel (4.05/4.38:1) — needs darker red, e.g. #c03030 (est 4.60:1)

## Recommendation
Run this script after any ui/tokens.css edit to catch regressions. Can be wired
into the cycle quality check or as a pre-commit hook.

## Cross-ref
- Builder patch: memory/ops/wcag-aa-light-theme-fixes-2026-11-23.md
- Hot note 2026-11-23: "9/21 pairs failing incl. --acc/--err near-misses"
- Prior a11y work: memory/builder/a11y_audit_increment1_2026-11-20.md
