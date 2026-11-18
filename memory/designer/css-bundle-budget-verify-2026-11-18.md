# Designer Goal #3: CSS Bundle Performance Budget - EVIDENCE (2026-11-18)

## Measurement
| File | Raw | Minified |
|------|-----|----------|
| ui/app.css | 22.3 KB | 20.2 KB |
| ui/core.js | 28.0 KB | 22.3 KB |
| ui/uploads.js | 33.3 KB | 27.3 KB |
| **TOTAL** | **83.6 KB** | **69.8 KB (71,463 B)** |

## Target: under 80 KB minified - PASS (69.8 KB, 10.2 KB under budget)

Minification method: comment stripping + whitespace collapse (no tool dependency).
This is conservative - a real minifier (esbuild/terser) would shave more.

## Top-5 Largest CSS Rules (app.css, post-comment-strip)
| # | Size | Selector |
|---|------|----------|
| 1 | 599 B | @media (max-width:375px) |
| 2 | 367 B | @media (max-width:768px) |
| 3 | 323 B | :root (token definitions) |
| 4 | 283 B | .opsbox |
| 5 | 251 B | .ft-tooltip |

## Top-5 Largest JS Functions (by line span)
### core.js
| # | Lines | Function |
|---|-------|----------|
| 1 | ~64 | stopBusy() - busy indicator state machine |
| 2 | ~35 | linkifyFiles(el, text) - file mention renderer |
| 3 | ~23 | actFollow() - panel jump logic |
| 4 | ~22 | addBubble(name, color, emoji, isYou) |
| 5 | ~21 | renderAgents() |

### uploads.js
| # | Lines | Function |
|---|-------|----------|
| 1 | ~55 | send() - message dispatch + optimistic UI |
| 2 | ~54 | attachRun(rid, startCursor) - run attachment |
| 3 | ~44 | (inline: donut chart render at L354) |
| 4 | ~41 | scanModels() - model inventory poller |
| 5 | ~36 | handleRunEvent(ev) - SSE event router |

## Optimization Assessment
No optimization required. Bundle is 10.2 KB under budget with headroom for growth.
If future additions push over 80KB, the largest targets would be:
- uploads.js send()/attachRun() (could extract to a composable module)
- app.css @media blocks (could consolidate responsive rules)

## Files checked
- ui/app.css sha12: ac3ef7ec2e35
- ui/core.js sha12: 485c08e3d384
- ui/uploads.js sha12: fb38dcbc5d0f

---

## RE-MEASUREMENT (Builder cross-assist, later same day)

Files changed after initial verification. New measurement:

| File | Raw | Minified (naive) | sha12 |
|------|-----|------------------|-------|
| ui/app.css | 26,894 B | ~24,004 B | 00d8401c7ebc |
| ui/core.js | 36,247 B | ~28,567 B | 2f339f7f9412 |
| ui/uploads.js | 35,765 B | ~29,293 B | 044a5f2b404c |
| **TOTAL** | **98,906 B (96.6 KB)** | **~81,864 B (79.9 KB)** | — |

⚠️ **REGRESSION WARNING**: headroom dropped from 10.2 KB → **128 bytes**. Budget still met but effectively at the limit.

### Top-5 JS Functions (current)
1. streamReplyCore() — 5,678 B (core.js)
2. goalsLoad() — 4,352 B (uploads.js)
3. send() — 2,942 B (uploads.js)
4. attachRun() — 2,873 B (uploads.js)
5. handleRunEvent() — 2,352 B (uploads.js)

### Recommendation
Add a CI size gate at 80 KB before closing goal 3; any further CSS/JS growth will breach budget.
