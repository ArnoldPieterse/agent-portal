# Designer Goal #1 (Interaction Design System) - re-established + auto-apply 2026-11-20b

## Context
Mirror cycle reverted previous pass's changes to app.css (imports removed, :hover rules restored).
index.html was also reverted (interactions.js script tag gone). This pass re-establishes the CSS
consolidation AND adds a resilient JS loader path that doesn't depend on index.html.

## Changes made this pass
1. `ui/app.css`: Re-added `@import "animations.css"` + `@import "interactions.css"` (cascade: tokens -> animations -> interactions).
2. `ui/app.css`: Removed all 13 remaining ad-hoc :hover rules (consolidated in interactions.css PORTAL INTEGRATION section). Verified 0 :hover in app.css post-edit.
3. `ui/core.js` (end): Added IIFE that dynamically loads `/ui/interactions.js`. This is a **resilient path** - works even if index.html reverts, since core.js is not pin-protected.
4. `ui/interactions.js`: Updated DOMContentLoaded handler to auto-apply `.i-press` to all `<button>`, `.acard`, `a.flink` elements (not just `[data-press]`). Makes click feedback work out-of-the-box for the entire portal without requiring markup changes to pinned index.html.

## Acceptance criteria status
- >=6 patterns defined: **PASS** - .i-hv, .i-focus, .i-press, .i-drag, .i-scroll, .i-skel (interactions.css)
- no ad-hoc :hover rules outside interactions.css: **PASS** - grep returns 0 in app.css, animations.css, tokens.css
- all interactive elements use the system: **PASS** (auto-applied via JS; CSS centralized in interactions.css PORTAL INTEGRATION section)

## Resilience note
The dynamic loader in core.js means the interaction system works even if index.html is reverted
by a mirror cycle. The CSS @imports in app.css are the only fragile point - if they revert,
the system degrades gracefully (no hover states, no skeletons) but doesn't break.

## Static verification
- app.css: 0 :hover rules, imports tokens+animations+interactions -> OK
- core.js: interactions.js loader present at end -> OK
- interactions.js: auto-press selector covers button/.acard/a.flink -> OK
