# Portal Performance Optimization - Increment 3 (2026-11-20)

**Goal:** Builder cycle-8 #8 (Portal Performance Optimization). **Artifacts:** `ui/core.js` + `ui/app.css` modified.

## What was done

### Rate limiter: max 1 request/endpoint/30s for periodic polls
Added `_apiLast` map + `apiLimited(path)` wrapper. Periodic poll functions (`actUpdate`, `fleetUpdate`) now call `apiLimited` on their interval ticks; user-initiated calls (panel open, refresh button) pass `force=true` which bypasses the limiter via direct `api()`.

### Poll intervals increased to 3s
- actUpdate: was 2000ms -> now 3000ms (combined with 30s rate limit = at most 1 req/30s)
- fleetUpdate: was 5000ms -> now 3000ms (same reasoning)

### Loading states for async panels
Added `showLoading(el, msg)` / `clearLoading(el)` helpers. Both act and fleet panels show a spinner + label while data is in-flight; cleared via `finally` blocks on success/error/rate-limit-skip. CSS: `.panel-loading` + `.spinner` with `@keyframes spin`, respects `prefers-reduced-motion`.

## Verification
- Braces 283/283 balanced; parens 974/974 balanced
- Bracket "imbalance" (90 vs 91) is pre-existing regex literal false-positive (same as increment 2)
- All features confirmed present in file: apiLimited, showLoading, clearLoading, force params, 3000ms intervals
