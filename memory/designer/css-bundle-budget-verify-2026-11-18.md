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
