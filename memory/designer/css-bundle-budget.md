# CSS Bundle Performance Budget — Measurement (2026-11-18)

## Baseline measurement
| File | Raw | Minified (est) | Savings |
|------|-----|----------------|----------|
| ui/app.css | 22,853b | 20,968b | 8.2% |
| ui/core.js | 28,641b | 22,805b | 20.4% |
| ui/uploads.js | 34,138b | 27,930b | 18.2% |
| **TOTAL** | **85,632b** | **71,703b** | — |

Target: <80,000 bytes minified → **PASS** (below by 8,297b / 10.4% headroom)

## Top-5 largest CSS rules (app.css, 219 rules total)
| Size | Selector |
|------|----------|
| 603b | @media (max-width:375px) block |
| 344b | :root custom properties |
| 285b | .opsbox |
| 253b | .ft-tooltip |
| 234b | .amenu |

## Notes
- No minification pipeline exists; savings are from comment/whitespace removal only.
- A proper minifier (esbuild, terser) would likely achieve the same or better.
- Largest single file is uploads.js (34.1b raw) — candidate for code-splitting if budget tightens.
- 219 CSS rules, 1 media query — compact; no bloat from unused selectors identified yet.

## Next steps (if budget tightens)
1. Run esbuild --minify on all three files for exact production numbers.
2. Tree-shake uploads.js if it grows past 40KB.
3. Add a CI check: fail if total minified >80KB.
