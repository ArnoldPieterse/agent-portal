# Density-Mode Selector Audit — 2026-11-24

## Context
HOT NOTES (2026-11-23) flagged: "CSS uses `data-density` attr but JS sets `cd--calm`/`cd--incident` classes — selector mismatch identified, needs alignment."

## Finding: NO MISMATCH EXISTS in current files

Searched all 15 UI files (`.css` + `.js`) for `density`, `calm`, `incident`, `data-density`, `cd--calm`, `cd--incident`:

| File | Hits |
|------|------|
| `ui/app.css` | 0 |
| `ui/core.js` | 4 (benchmark harness only) |
| `ui/cockpit-layout.css` | 1 (comment: "Reduce padding for mobile density") |
| `ui/cockpit-risks.css` | 1 (prose comment: "calm check + neutral copy") |

**No `data-density` attribute, no `.cd--calm`, no `.cd--incident` selectors exist anywhere.**

## What core.js actually does (lines 505-534)
A **benchmark harness**: swaps the stylesheet link between `app_density_before.css` and `app.css`, measures render time delta, outputs `{before, after}`. It is NOT a runtime calm/incident mode toggle.

## Conclusion
The "selector mismatch" was a forward-looking note about Designer's open goal #1 (Adaptive Information Density — calm vs incident modes), which is **unbuilt**. There is no live bug to fix; the feature simply doesn't exist yet. When Designer implements it, both CSS and JS must use the same mechanism (attribute or class) consistently.

## Action
- No code change needed now.
- If/when Designer ships goal #1, Verifier will re-audit for selector consistency as part of the Playwright gate.
