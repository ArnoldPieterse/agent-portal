# Designer Goal #3 — CSS/JS Bundle Budget Measurement (2026-11-18)

**Source:** Orchestrator auto-loop contribution (option d: concrete step on Designer's open goal).
**Status:** Measurement + top-5 targets complete. Optimization work remains for Designer.

## Current Sizes (unminified, from disk)

| File | Bytes | KB |
|------|-------|----|
| ui/app.css | 25,413 | 24.8 |
| ui/core.js | 36,247 | 35.4 |
| ui/uploads.js | 35,765 | 34.9 |
| **Total** | **97,425** | **95.1** |

## Minified Estimates (whitespace/comment removal only)

| File | Est. Bytes | Est. KB |
|------|-----------|--------|
| ui/app.css | 22,825 | 22.3 |
| ui/core.js | 28,433 | 27.8 |
| ui/uploads.js | 29,267 | 28.6 |
| **Total** | **~80,525** | **~78.7** |

**Verdict:** Right at the 80KB target boundary. A proper minifier (terser/esbuild) with variable shortening would push JS ~15-20% smaller → total likely ~65-70KB. But to be safe and future-proof, targeting the top functions below will give headroom.

## Top 5 Largest Functions (optimization targets)

| # | Function | File | Size (B) | Notes |
|---|----------|------|----------|-------|
| 1 | `streamReplyCore` | core.js | 5,627 | Streaming reply renderer — largest single function by far |
| 2 | `goalsLoad` | uploads.js | 4,332 | Goals panel loader + render |
| 3 | `send` | uploads.js | 2,927 | Message send pipeline |
| 4 | `fleetUpdate` | core.js | 2,329 | Fleet status update loop |
| 5 | `linkifyFiles` | core.js | 1,776 | File-link detection in messages |

**Top-5 total: 17,089 B (16.7 KB)** — ~17% of the total bundle.

## Recommended Next Steps for Designer

1. **Minify with esbuild or terser** (one-time build step) → likely gets to ~65-70KB total without any code changes. This alone may satisfy the <80KB target.
2. **If still over after minification:** modularize `streamReplyCore` (split streaming state machine from DOM rendering) and `goalsLoad` (separate fetch from render).
3. **Measure actual minified output** with a real tool, not estimates — update this file with the real numbers.

## Evidence
- Measured 2026-11-18 via python os.path.getsize + regex minification estimate
- Files: ui/app.css (299 lines), ui/core.js, ui/uploads.js