# CSS Bundle Performance Budget - Measurement Report
**Date:** 2026-11-17
**Goal:** #2 (CSS bundle performance budget)
**Acceptance criteria:** Measure total transfer size; target <80 KB minified; identify top-5 largest rules.

## Results

| File | Unminified | Minified (est.) |
|------|-----------|-----------------|
| ui/app.css | 22,853 B (22.3 KB) | 20,724 B (20.2 KB) |
| ui/core.js | 28,641 B (28.0 KB) | 21,999 B (21.5 KB) |
| ui/uploads.js | 34,138 B (33.3 KB) | 27,080 B (26.4 KB) |
| **Total** | **85,632 B (83.6 KB)** | **69,803 B (68.2 KB)** |

## Verdict: PASS
Minified total = 68.2 KB < 80 KB budget (11.8 KB headroom).

## Top-5 largest CSS rule blocks (ui/app.css)

| Rank | Bytes | Selector |
|------|-------|----------|
| #1 | 748 | Header comment block (FleetTopology diagram section) |
| #2 | 604 | File header comment (design tokens + modularity note) |
| #3 | 601 | @media (max-width:375px) - mobile breakpoint container |
| #4 | 453 | @media (max-width:768px) - tablet breakpoint container |
| #5 | 285 | .opsbox - operations panel styles |

## Key Observations
1. No single "fat rule" - largest individual selector block is 748 bytes (a comment). Distribution is flat: top-10 rules = only 17.6% of total CSS bytes.
2. Comments are the biggest removable weight - the two header comments alone are ~1.3 KB unminified (~6% of app.css). A minifier strips these automatically.
3. JS is the heavier file - uploads.js (34 KB) and core.js (28 KB) dominate; CSS is only 27% of total weight.
4. No optimization needed to meet budget. The 11.8 KB headroom absorbs future additions comfortably.

## Recommendations (for next cycle, not blocking)
- If strict unminified budget matters: strip the two header comments to save ~1.3 KB (brings unminified total to ~82.3 KB).
- Real optimization lever is JS: consider lazy-loading uploads.js only when upload UI is visible (saves 26.4 KB initial transfer).
- Add a CI check: total_minified < 80*1024 to prevent regression.

## Method
- Minification estimated by regex (strip comments, collapse whitespace, remove spaces around punctuation). Actual minifier (e.g. terser, cssnano) may produce slightly different results.
- Rule block parsing: brace-matching on ui/app.css source; @media counted as single container block.
