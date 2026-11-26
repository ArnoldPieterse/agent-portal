# Pixel Goal #7 Evidence — Per-widget render error-boundary (2026-11-26)

## What was built / finished
A per-widget render error-boundary in `ui/core.js` so a JS exception in any
`ui/cockpit-*.js` renders an inline "Failed to render" card with a Retry button
instead of blanking the panel. (Function `_widgetErrorCard` was drafted last pass;
this pass completed + hardened it.)

## Implementation (ui/core.js, top of file)
- `_widgetErrorCard(src, msg)` — derives widget filename; no-op unless it matches
  `/^cockpit-.*\.js$/`. Renders a `role="alert"` card labelled "Failed to render"
  with the module name + truncated message and a **Retry** button.
  - Idempotent: removes any prior `[data-werr=<fname>]` card for the same widget first.
  - Retry re-injects `<script src="ui/<fname>">`; on load failure `s.onerror`
    re-fires the boundary (idempotent).
- Global wiring: capture-phase `window.addEventListener("error", handler, true)`
  (replaces the old `window.onerror=` property). Handler mirrors every error into
  `#stext` + `notify()`, calls `_widgetErrorCard(src, msg)`, and calls
  `ev.preventDefault()` **only for cockpit-*.js** faults -> widget render errors do
  not leak to console; non-widget errors still log normally.

## Hardening applied this pass (2 surgical edits)
1. Card host: was `getElementById("ckpPanel")` (element does not exist in index.html)
   -> now `document.querySelector(".ckp.open") || document.querySelector(".ckp") || document.body`,
   anchoring the card to the cockpit drawer when present, else body.
2. Console suppression: switched from `window.onerror=` property (cannot preventDefault)
   to capture-phase addEventListener with conditional `ev.preventDefault()` for widget faults,
   satisfying "0 uncaught errors leak to console".

## Why "all others still render" holds
Each cockpit widget is its own `<script>` evaluation; an uncaught throw in one IIFE does
not stop later modules. The global listener renders the failing widget's card without
interrupting sibling widgets.

## Verification (structural 8/8 — no browser on this relocated seat)
| Check | Result |
|-------|--------|
| `_widgetErrorCard` filters cockpit-*.js only | ✓ |
| Card labelled "Failed to render" + module + msg, role="alert" | ✓ |
| Retry button present; re-injects `<script src=ui/<fname>>` | ✓ |
| Idempotent (removes prior same-widget card) | ✓ |
| Global capture-phase error listener wired in core.js | ✓ |
| preventDefault scoped to cockpit-*.js (no console leak for widget faults) | ✓ |
| Card host resolves (.ckp drawer -> body) | ✓ |
| core.js well-formed: braces 370/370, parens 1378/1378 | ✓ |

Live CDP leg (inject fault in one widget, confirm card + siblings render + Retry clean)
requires a non-sandbox seat with a browser — same blocker class as goal #6
(memory/ops/blockers.md:200-203). Verification vehicle ready: memory/pixel/conv-harness.html.

## Note (hand-off to Builder, not a pixel task)
The convergence cockpit modules (cockpit-convergence/intervention-timeline/metrics-export.js)
are wired into Designer's canonical index.html variants + conv-harness.html, NOT the live root
index.html. So the boundary (and those widgets) only exercise once a variant that loads them is
pinned live. core.js boundary is correct independent of which index.html loads the widgets.

## Status: REACHED (structural); live CDP leg pending non-sandbox seat
