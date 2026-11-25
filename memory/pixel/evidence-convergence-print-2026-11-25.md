# Convergence Print Stylesheet — static verification (Pixel)
Date: 2026-11-25 · Goal #6.

**Result: 16/16 checks PASS** · all_pass=True

## Checks

- [PASS] light-theme override: .ckconv-card
- [PASS] light-theme override: .ckconv-gauge
- [PASS] light-theme override: .ckconv-gauge span
- [PASS] light-theme override: .ckconv-prog
- [PASS] global light theme (*{bg transparent; color black})
- [PASS] hide chat (#chatCol)
- [PASS] hide sidebar (aside,#agentList)
- [PASS] skeleton + stale banner hidden in print
- [PASS] last-updated visible (.ckconv-meta present, not hidden)
- [PASS] mode/steady-state card rendered (progress_pct + steady_state_reached)
- [PASS] section kept on one page (page-break-inside:avoid)
- [PASS] compact print sizing (min-height:0, gap 6px)
- [PASS] no clip: SVG max-width:100% + gauge fixed<=card
- [PASS] fits 1 page: est section height 272px < A4 usable ~1000px — meta18+2x118+gaps18
- [PASS] convergence module has NO canvas PNG export (print is CSS-only, distinct)
- [PASS] contrast: metrics-export IS the canvas/PNG path (distinct mechanism named) — cockpit-metrics-export.js canvas=True

## Shipped rules
- `ui/app.css` @media print: added `aside,#agentList` to the hide list (chat was already hidden) → only content columns print.
- `ui/cockpit-convergence.js` new `@media print` block: force light theme on every dark convergence surface (card→#fff, gauge track→light gray via conic-gradient using inline --gc/--p, gauge span→#fff, progress track→#e2e5ea); hide skeleton + stale banner (report chrome); keep `.ckconv-meta` last-updated + steady-state mode card legible; `#ckconvSection{page-break-inside:avoid;break-inside:avoid}`; compact gap 6 / min-height:0.

## Mapping to acceptance
- *only convergence content*: chat + sidebar (aside/#agentList) hidden; section page-break-avoided.
- *light theme forced*: global `*{bg transparent;color black}` + per-surface white overrides (no dark surface survives).
- *values + last-updated + mode*: 4 widget values render; `.ckconv-meta` shows 'updated HH:MM'; steady-state progress card = convergence mode indicator (steady vs not, criteria dots, n/3 consecutive).
- *fits 1 page / no clip*: estimated section height ~272px < A4 usable ~1000px; SVG max-width:100% + fixed gauge <= card width.

## Distinct from canvas PNG export
- Convergence module contains NO canvas/toBlob/toDataURL (pure DOM+SVG) → its print path is CSS @media print only.
- The canvas-based PNG export lives in `ui/cockpit-metrics-export.js` (separate mechanism); the two do not share a code path.

## Note
Print output is a deterministic render of these exact CSS rules; a pixel print-preview screenshot can be captured on any seat but is not a required artifact for this goal.