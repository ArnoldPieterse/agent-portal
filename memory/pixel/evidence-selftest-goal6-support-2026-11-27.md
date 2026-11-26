# Pixel — Goal #6 unblock support: in-page self-test function (2026-11-27)

## What was done
Added `window.__ckconvSelfTest()` IIFE to `ui/cockpit-convergence.js` (appended after main module, no new script tag needed).

## Purpose
Simplifies the non-sandbox CDP run for goal #6 closure. Instead of complex DOM queries in the external CDP script, the seat operator can:
1. Open http://localhost:8099/ at @375 and @768
2. Call `window.__ckconvSelfTest()` in DevTools console (or via CDP Runtime.evaluate)
3. Get back structured JSON: `{pass, overflow, widgets[4]}`

## Verification (structural)
- 4 data-testid selectors confirmed present in cockpit-convergence.js source: ckconv-score, ckconv-metrics, ckconv-intv-spark, ckconv-timeline ✓
- No new dependencies; uses only document.querySelector + getBoundingClientRect + documentElement.scrollWidth/clientWidth
- IIFE pattern matches existing module style; no globals leaked except the named `window.__ckconvSelfTest`
- Delimiter balance in appended block: verified (braces 4/4, parens balanced)

## Impact on unblock command
The existing `cdp_375_dom_check.py` still works as-is. This is a BONUS simplification: if the CDP script has issues, a manual DevTools call suffices. No change to the one-command unblock path.

## File changed
- ui/cockpit-convergence.js (+38 lines, appended self-test IIFE)
