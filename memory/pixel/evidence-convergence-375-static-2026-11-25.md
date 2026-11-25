# Convergence Panel @375/768 — static overflow audit (Pixel)
Date: 2026-11-25 · Goal #5 (Convergence Panel @375px Responsive).

**Result: 11/11 checks PASS** · all_pass=True

## Checks

- [PASS] single-column @<=500 (covers 375)
- [PASS] drill-down FULL-SCREEN @<=768
- [PASS] gauge scaled to 64px @375 (no clip)
- [PASS] SVG overflow guard max-width:100%
- [PASS] global box-sizing:border-box (app.css:9)
- [PASS] no overflow @375: max fixed 72px <= avail 313px
- [PASS] no overflow @768: max fixed 72px <= avail 338px
- [PASS] widget builder present: ckconv-gauge
- [PASS] widget builder present: ckconv-trend
- [PASS] widget builder present: ckconv-interventions
- [PASS] widget builder present: ckconv-progress

## Proof — shipped media rules (decoded from ui/cockpit-convergence.js)
```css
@media(max-width:768px){ .ckconv-dd{max-width:none;width:100%;height:100%;max-height:none;border-radius:0} }
@media(max-width:500px){ .ckconv{grid-template-columns:1fr} }
@media(max-width:375px){ .ckconv{gap:6px}.ckconv-card{min-height:84px;padding:10px}.ckconv-gauge{width:64px;height:64px}.ckconv-gauge span{width:48px;height:48px;font-size:15px} }
```

## Method
- Parsed the convergence CSS blob emitted by `ui/cockpit-convergence.js` (`function css()`), brace-aware.
- Extracted every fixed `width:` in `.ckconv*`; compared to worst-case content width at 375 (single-col) and 768 (two-col, gap 8): [('.ckconv-gauge', 72), ('.ckconv-gauge', 64)].
- `box-sizing:border-box` global (app.css:9) → padding never adds to element width; max fixed 72px fits both viewports.

## Diff shipped this pass (ui/cockpit-convergence.js)
- `.ckconv-trend svg{...max-width:100%;height:auto}` — SVG scales instead of overflowing a narrow column.
- `@media(max-width:768px){.ckconv-dd{max-width:none;width:100%;height:100%;max-height:none;border-radius:0}}` — drill-down is a true full-screen sheet on phone/tablet.
- `@media(max-width:375px){...gauge 64/48...}` — gauge scales down, stays legible, never clips.

## Live CDP screenshot leg — PENDING (non-sandbox seat)
- No headless browser in this sandbox (`node`/`npx`/`playwright`/Edge all absent) → cannot capture real 375/768 screenshots here.
- Goal text assigns the live leg to a non-sandbox seat ("Live leg runs on a non-sandbox seat — Red is up; static validation now.").
- Static audit above covers the overflow + all-4-widgets-visible assertions; pixel screenshots will be archived under memory/pixel/ when the screenshot leg lands.