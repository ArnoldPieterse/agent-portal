# Builder verification: Designer Goal #1 token audit - 36 remaining hard-coded hex
Date: 2026-11-18 | method: independent re-parse of ui/app.css (sha12=b72f1bfb4f91)

## Result: CONFIRMED FAIL, count = 36 (matches ORCH-VERIFY 2026-11-18)

Acceptance test: zero hex colors in app.css OUTSIDE token-definition blocks.
Two token blocks hold legitimate literal hex and are excluded:
  - :root (dark theme)      lines 6-7
  - [data-theme=light]      lines 11-12  (comment L8: 'literal values ONLY, never var()')
All other hex = hard-coded component-rule values that must become var(--token).

## The 36 offending values (line: value)
- L28: `#20304d`
- L34: `#2a3342`
- L39: `#3a6fd6`
- L39: `#fff`
- L46: `#243b63`
- L46: `#33507f`
- L54: `#3ddc84`
- L62: `#2a3342`
- L64: `#4a3f6b`
- L65: `#b79ce0`
- L71: `#fff`
- L86: `#ff6b6b`
- L104: `#fff`
- L106: `#8b93a7`
- L108: `#6db1ff`
- L109: `#9ccaff`
- L110: `#141a26`
- L110: `#2c3548`
- L110: `#cdd3e0`
- L111: `#2c3548`
- L111: `#9ccaff`
- L112: `#8b93a7`
- L113: `#aab2c5`
- L124: `#888`
- L125: `#ffb454`
- L127: `#e05252`
- L185: `#0d1117`
- L187: `#8b949e`
- L189: `#30363d`
- L189: `#58a6ff`
- L191: `#8b949e`
- L192: `#c9d1d9`
- L193: `#8b949e`
- L194: `#d29922`
- L194: `#2d2000`
- L194: `#e3b341`

## Recommended closure for Designer (one concrete path)
1. Add the missing semantic tokens to BOTH :root and [data-theme=light] that these 36 values represent.
2. Group by usage family: selected/hover surface (#20304d,#2a3342), active seg (#3a6fd6/#fff),
   status/error accents, code-block palette (L185-194 GitHub-dark set).
3. Replace each L# value with var(--token); re-run this parser -> expect 0 outside token blocks.

Parser note: an earlier naive count of '60 total / 48 outside :root' was wrong because it did not
exclude the [data-theme=light] block. Correct exclusion yields exactly 36, matching ORCH-VERIFY.
