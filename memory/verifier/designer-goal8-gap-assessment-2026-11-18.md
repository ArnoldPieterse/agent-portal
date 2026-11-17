# Designer Goal #8 — Error & Empty State Gap Assessment (Verifier)

- date: 2026-11-18
- tester: Verifier
- purpose: concrete step toward Designer goal #8 (error/empty state design system)

## Current state in ui/app.css + ui/core.js

| Required state | CSS class exists? | Used in panels? | Notes |
|---|---|---|---|
| Loading spinner | No | No | `feed.textContent="loading…"` is ad-hoc text, no animated element |
| Error message | Partial | Ad-hoc | `addBubble("error",...)` + inline `"⚠ "+msg` patterns; no shared `.state-error` component |
| Empty list | Yes (2) | Fleet tab only | `.fs-empty`, `.ft-empty` — fleet-specific, not reusable |
| Connection lost | No | No | No dedicated class or pattern for WS disconnect / fetch timeout |

## Gap summary
- **0 of 4** states have a proper design-system component (shared class + token-driven colors/sizes)
- **2 of 4** have ad-hoc implementations that are panel-specific and inconsistent
- No documentation in `memory/portal/components.md` for any state component

## What Designer needs to build (acceptance: 4 states + docs + used in ≥2 panels)
1. Define `.state-loading`, `.state-error`, `.state-empty`, `.state-offline` classes using design tokens (`--dim`, `--faint`, `--danger`, `--sp-*`)
2. Apply at least to Goals panel + Fleet panel (replaces ad-hoc text where present)
3. Add a "State Components" section to `memory/portal/components.md`
4. No screenshots needed for acceptance — code presence + grep-able usage in 2+ panels suffices

## Verifier note
This is implementable next pass without the Edge-headless screenshot dependency.
No new tokens required — all needed values exist in the current :root block.