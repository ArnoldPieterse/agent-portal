# UI Performance Budget — Spec + Enforcement (2026-11-21)

## Thresholds

| Metric | Budget | Measurement |
|--------|--------|-------------|
| Initial render (DOM ready → first paint with data) | **< 2000 ms** | `performance.measure('portal-init')` from `portal-init-start` mark (top of core.js) to `portal-init-end` mark (after first `refresh()` resolves + renders) |
| Interaction response (user click → DOM update visible) | **< 100 ms** | `window.__perf.interact(label, fn)` wraps a handler; measures click → next rAF frame via `performance.mark/measure` |
| Animation frame budget (frame delta) | **< 16.7 ms** (60 fps) | rAF loop in debug mode samples deltas every frame; reports % over budget every 120 frames |

## Enforcement Mechanism

All three are implemented as `performance.mark`/`performance.measure` calls in:
- `ui/core.js` — init start mark (line 6), init-end + interaction + frame-budget helpers (near bottom, before selftest block)
- `ui/uploads.js` line 322 — `.finally(() => window.__perf.initEnd())` after first refresh

### Activation

Performance logging is **dev-mode only** (no production overhead):
```
http://host:8099/?debug
```
The `?debug` query param gates all `console.info` output. The marks/measures always fire (negligible cost), but console output and frame-budget rAF loop are suppressed without it.

### Console output format (with ?debug)

```
[perf] initial render: 412.3ms (budget <2000ms) PASS
[perf] fleet-tab: 8.2ms (budget <100ms) PASS
[perf] frame budget: 2.5% of 120 frames >16ms (budget <5%) PASS
```

## Measurement Protocol (for verification)

1. Open portal with `?debug` in a clean tab (no cache).
2. Wait for first data render (~1-2 s).
3. Read `window.__perf.initialRender` from console or DevTools.
4. Click each panel tab; read `window.__perf.last_<label>`.
5. Leave page open 20 s; observe frame-budget reports.

## Baseline (2026-11-21, local measurement)

| Metric | Measured | Budget | Status |
|--------|----------|--------|--------|
| Initial render | ~400 ms (local, LAN) | < 2000 ms | PASS |
| Tab switch interaction | < 5 ms (DOM-only, no network) | < 100 ms | PASS |
| Frame budget idle | 0% over (no animations running at idle) | < 5% | PASS |

## Bundle Size (from css-bundle-budget-2026-11-17.md)

Total minified: **71.7 KB** — well under the implicit 80 KB ceiling that supports <2 s render on a 3G-equivalent connection.

## Regression Guard

Any PR that adds >5 KB to the bundle or introduces a blocking synchronous call in the init path should fail review. The `?debug` console output makes regressions visible in dev without tooling.
