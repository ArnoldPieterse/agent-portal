# Evidence: WCAG AA Contrast Fix (Goal 3)
Date: 2026-11-15

## Method
Computed relative luminance and contrast ratio for every text/background pair in the portal CSS
(both :root tokens and non-token hex values). Checked against WCAG 2.1 AA threshold (≥4.5:1 normal, ≥3.0:1 large).

## Results — All pairs pass after fix
| Pair | Ratio | Status |
|------|-------|--------|
| --text on --bg | 16.08:1 | ✓ |
| --dim on --bg | 7.74:1 | ✓ |
| --dim on --panel | 7.15:1 | ✓ |
| --faint on --panel2 | 5.45:1 | ✓ |
| --acc on --bg | 5.88:1 | ✓ |
| btn-primary (--bg text on --acc) | 5.88:1 | ✓ (fixed from 3.22:1) |
| seg .on (#fff on #3a6fd6) | 4.75:1 | ✓ |
| busyspan (#8b93a7 on --panel) | 5.68:1 | ✓ |
| .flink (#6db1ff on --panel) | 7.80:1 | ✓ |
| .dmseg summary (#b79ce0 on ~#1e1530) | 7.34:1 | ✓ |
| peek .pk-sz (#8b93a7 on #141a26) | 5.67:1 | ✓ |
| queue text (#c9d1d9 on #0d1117) | 12.26:1 | ✓ |
| intBanner (#e3b341 on #2d2000) | 8.19:1 | ✓ |

## Fix applied
Single change: `.btn-primary` color changed from `#fff` to `var(--bg)` (dark text on accent blue).
Before: white on #4f8cff = 3.22:1 (FAIL for normal text)
After: #0e1116 on #4f8cff = 5.88:1 (PASS)

File: index.html L147 (.btn-primary rule)
