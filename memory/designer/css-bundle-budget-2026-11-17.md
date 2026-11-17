# CSS Bundle Performance Budget — Evidence (2026-11-17)

## Measurement

| File | Raw | Minified (naive regex) |
|------|-----|------------------------|
| ui/app.css | 24,254 B (23.7 KB) | 22,047 B (21.5 KB) |
| ui/core.js | 29,454 B (28.8 KB) | 23,473 B (22.9 KB) |
| ui/uploads.js | 34,138 B (33.3 KB) | 27,930 B (27.3 KB) |
| **TOTAL** | **87,846 B (85.8 KB)** | **73,450 B (71.7 KB)** |

## Target: <80 KB minified → **MET** (71.7 KB, 9.3 KB headroom)

No optimization required — bundle is already within budget after standard whitespace/comment stripping.

## Top-5 Largest CSS Rules

| # | Size | Selector |
|---|------|----------|
| 1 | 601 B | @media (max-width:375px) { … } |
| 2 | 369 B | @media (max-width:768px) { … } |
| 3 | 325 B | :root { --token definitions } |
| 4 | 109 B | #modeBar button:focus-visible, .seg button:focus-visible { … } |
| 5 | ~100 B | (next largest interactive-state rule) |

No single rule exceeds 601 bytes; no modularization needed.

## Top-5 Largest JS Functions

| # | Size | Function | File |
|---|------|----------|------|
| 1 | 5,684 B | streamReplyCore() | core.js |
| 2 | 2,948 B | send() | uploads.js |
| 3 | 2,879 B | attachRun() | uploads.js |
| 4 | 2,746 B | goalsLoad() | uploads.js |
| 5 | 2,352 B | handleRunEvent() | uploads.js |

streamReplyCore() is the only function >3 KB; it handles SSE stream parsing + DOM append and is cohesive — splitting would add indirection without size gain.

## Conclusion

Budget met. No git diff needed (no code changes). Measurement recorded as baseline for future regression tracking.
