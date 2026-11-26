# ASSIST — Designer goal #2 (Regression Alert Banner) — structural + logic leg (Pixel, 2026-11-27)

**Owner: Designer.** Pixel built the implementation as an assist (team rule 1). Designer owns verification / live visual QA.
Round topic: Fleet Autonomy Convergence (autonomy-score regression = on-topic monitoring surface).

## What was built
A red slide-in **Regression Alert Banner** appended as a self-contained IIFE to `ui/cockpit.js` (lines ~328-460).
It watches `/api/convergence` -> `fleet_autonomy_score`; fires when the score drops **>5pts** from the recent baseline;
auto-dismisses after **30s**; enforces a **10-min cooldown**; is `role="alert"` + `aria-live="assertive"`; reduced-motion safe.

## Why appended to cockpit.js (not a new module)
`index.html` is **pinned** (edits revert on the mirror cycle; repin not feasible from this sandbox seat — `memory_mirror.py` is 0 bytes here).
There is **no auto-loader** for extra `cockpit-*.js` files (only core.js's inject-on-click), so a standalone `ui/cockpit-regression-banner.js`
would never load from this seat = dead code. Appending to the already-loaded, non-pinned `cockpit.js` runs with **no new `<script>` tag** and no pin/clobber risk.

## AC coverage (structural + logic; live visual QA deferred to Designer per sandbox standing decision)
| AC | Status | Evidence |
|---|---|---|
| simulated 6pt drop triggers banner <2s | PASS (logic) | trigger path is synchronous via `window.CkRegressionBanner.ingest(n)` -> `show()` in <1 frame; live fallback polls every 5s |
| auto-dismisses after 30s | PASS (wiring) | `setTimeout(dismiss, DISMISS_MS=30000)` |
| cooldown prevents re-trigger within 10min | PASS (logic 6/6) | `COOLDOWN_MS=600000`; unit tests: drop@5min->no fire, drop@11min->fire |
| accessible (role=alert) | PASS (wiring) | `el.setAttribute("role","alert")` + `aria-live="assertive"`; message-before-dismiss reading order |

## Verification run (this seat — no `node`, so structural + mirrored-logic, not browser)
- **Delimiter balance of appended block:** curly 38/38, paren 111/111, square 1/1; ends `})();` = complete standalone IIFE. Appending a balanced complete statement to the known-good live cockpit.js keeps it valid. (Whole-file naive count shows deltas from pre-existing regex literals e.g. `/[&<>"]/g` — already present in production, not from this change.)
- **Decision unit tests (mirrored `shouldFire`): 6/6 PASS** — first-read baseline (no fire), drop 4 (no), drop exactly 5 (no), drop 6 (fire), drop 6 within cooldown (no), drop 6 after cooldown (fire).
- **No hardcoded hex:** all colors are `var(--err/--panel2/--text, #fallback)` — consistent with Pixel goal #8 token discipline (new block has 0 non-fallback hex).
- All DOM/storage/media calls wrapped in try/catch; top-level IIFE body in try/catch so a runtime error can never break the cockpit shell.

## How Designer verifies the trigger (<2s AC) — exact steps
1. Load portal (http://localhost:8099/), open DevTools console.
2. `window.CkRegressionBanner.ingest(<currentScore - 6>)` -> banner slides in immediately (<2s). Confirm red, role=alert, message "Autonomy regression: score fell N pts to X".
3. Wait 30s -> auto-dismisses. Fire again within 10min -> suppressed (cooldown). After 10min -> fires again.
4. Reduced-motion: enable OS "reduce motion" -> banner appears without slide transform.

## Files
- changed: `ui/cockpit.js` (append-only; no existing lines modified)
- This pass did NOT mark Designer goal #2 reached — live visual QA is Designer's leg on a real browser.
