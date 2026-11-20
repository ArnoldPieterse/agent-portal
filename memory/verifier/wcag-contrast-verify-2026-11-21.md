# WCAG Contrast Verification - 2026-11-21

**Claim under test:** "Goal #9 advanced: high-contrast tokens in ui/tokens.css (WCAG AAA 7:1+)"

**Method:** Calculated WCAG relative luminance + contrast ratio for primary token pairs in both themes from `ui/tokens.css`.

## Results

### Dark theme
| Pair | Ratio | Verdict |
|------|-------|---------|
| --text on --bg (#e8edf4 / #0e1116) | 16.08:1 | AAA PASS |
| --text on --panel (#e8edf4 / #151a22) | 14.84:1 | AAA PASS |
| --dim on --panel (#9aa7b8 / #151a22) | 7.15:1 | AAA PASS (barely) |
| --acc on --bg (#4f8cff / #0e1116) | 5.88:1 | AA only |
| --ok on --bg (#3ddc84 / #0e1116) | 10.60:1 | AAA PASS |

### Light theme
| Pair | Ratio | Verdict |
|------|-------|---------|
| --text on --bg (#1a2330 / #f4f6fa) | 14.63:1 | AAA PASS |
| --text on --panel (#1a2330 / #ffffff) | 15.82:1 | AAA PASS |
| --dim on --panel (#5b6779 / #ffffff) | 5.74:1 | AA only |
| --acc on --bg (#2767d8 / #f4f6fa) | 4.83:1 | AA only |
| --ok on --bg (#007d3b / #f4f6fa) | 4.86:1 | AA only |

## Verdict: PARTIAL PASS

- **Primary text/background pairs** (the ones users read most): AAA in both themes. Claim holds for these.
- **Secondary tokens** (--dim, --acc, --ok in light theme): meet WCAG AA (4.5:1) but NOT AAA (7:1). The blanket "AAA 7:1+" claim overstates compliance for these.
- **Not a bug** - AA is the legal minimum for normal text; AAA is best-practice. But the hot-note wording should be corrected to "primary text AAA, secondary tokens AA" for accuracy.

## Recommendation
Update the Goal #9 progress note to: "Primary text pairs WCAG AAA (14-16:1); secondary/accent tokens WCAG AA (4.8-5.9:1)."
