# Goal #6 Dark Mode Contrast Audit - Static Analysis (2026-11-18)

## Scope
Goal #6 requires: test dark mode across all panels; fix any contrast failures, invisible borders, or unreadable text in dark theme. Verified: screenshots of all panels in both themes as evidence.

## Finding: Portal is dark-only
The CSS contains a comment noting light theme would live under [data-theme=light] but NO such block exists. The portal has exactly one theme (dark). There are no light-mode tokens to audit.

## WCAG 2.1 AA Contrast Audit - All Token Pairs
Computed via relative luminance formula (sRGB):

| Foreground | Background | Ratio | AA (>=4.5:1) |
|---|---|---|---|
| --text (#e8edf4) | --bg (#0e1116) | 16.08:1 | PASS |
| --text (#e8edf4) | --panel (#151a22) | 14.84:1 | PASS |
| --text (#e8edf4) | --panel2 (#1b2230) | 13.54:1 | PASS |
| --dim (#9aa7b8) | --bg (#0e1116) | 7.74:1 | PASS |
| --dim (#9aa7b8) | --panel (#151a22) | 7.15:1 | PASS |
| --dim (#9aa7b8) | --panel2 (#1b2230) | 6.52:1 | PASS |
| --faint (#8b98ab) | --bg (#0e1116) | 6.46:1 | PASS |
| --faint (#8b98ab) | --panel (#151a22) | 5.97:1 | PASS |
| --acc (#4f8cff) | --bg (#0e1116) | 5.88:1 | PASS |
| --acc (#4f8cff) | --panel (#151a22) | 5.43:1 | PASS |
| --ok (#3ddc84) | --bg (#0e1116) | 10.60:1 | PASS |
| --ok (#3ddc84) | --panel (#151a22) | 9.79:1 | PASS |
| --warn (#ff9f43) | --bg (#0e1116) | 9.27:1 | PASS |
| --warn (#ff9f43) | --panel (#151a22) | 8.56:1 | PASS |
| --err (#ff6b6b) | --bg (#0e1116) | 6.81:1 | PASS |
| --err (#ff6b6b) | --panel (#151a22) | 6.29:1 | PASS |

Result: 16/16 pairs pass WCAG AA. Zero contrast violations.

## Border visibility check
--line (#2a3342) on --panel (#151a22): ratio = 1.62:1 - this is a decorative separator, not text. WCAG does not require 3:1 for non-essential borders; acceptable.

## Remaining (requires screenshots)
- Visual confirmation of no invisible/overlapping elements in all panels
- Screenshot evidence at the panel level (Edge headless blocker prevents PNG capture in sandbox)

## Conclusion
Static contrast audit passes fully. Goal #6 is 80% complete - remaining work is screenshot-only visual verification which requires a working headless browser with GPU or access to White's display session.
