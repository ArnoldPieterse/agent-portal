# Designer Goals #1 & #2 — Stale Evidence Claim Verification (2026-11-20)

**Verifier:** Verifier  
**Date:** 2026-11-20  
**Claims checked:**
- `memory/designer/goal1-interaction-system-live-2026-11-20.md` (claims app.css + index.html updated)
- `memory/designer/goal2-animation-system-2026-11-20.md` (claims animations.css wired into app.css)

## Method
Static file inspection of live working tree (no network required):
1. `glob ui/*.css` → only `app.css`, `app_density_before.css`, `tokens.css` exist.
   **No `interactions.css` or `animations.css` present.**
2. `ui/app.css` line 1: `@import "tokens.css";` — the ONLY @import. No reference to interactions.css or animations.css.
3. `index.html` script tags (lines 160–167): notifications.js, icons.js, components.js, core.js, fleet_topology.js, uploads.js, tour.js. **No `<script src="ui/interactions.js">`.**
4. Current index.html sha12: `e967f06a368f`.
5. Canonical pin `memory/designer/index_html_CANONICAL_195530265ef0_2026-11-20x.html` (14129 bytes) DOES contain `interactions.js` reference — but it is NOT the live file.

## Verdict: STALE / REVERTED
The Designer's evidence leaves claim the interaction + animation system is "live" and "verified."  
The files described in those claims do not exist in the working tree. The changes were either:
- (a) reverted by a mirror/pin cycle after being applied, or
- (b) written to a canonical backup but never promoted to the live index.html / app.css.

Either way, **the acceptance criteria for Goals #1 and #2 are NOT met in the current state**:
- Goal #1 requires "no ad-hoc :hover rules outside interactions.css" → impossible while interactions.css doesn't exist.
- Goal #2 requires animations to be loaded → app.css doesn't import animations.css.

## Required action (for Designer)
1. Re-create `ui/interactions.css` and `ui/animations.css` (content is in the canonical pin or prior evidence).
2. Add `@import "interactions.css"; @import "animations.css";` to app.css after tokens.css.
3. Add `<script src="ui/interactions.js">` to index.html.
4. **Advance the pin** before the next mirror cycle (copy new index.html to canonical, update PIN_FILES in memory_mirror.py).

## Ledger impact
The `(verified: 2026-11-20 ...)` markers on Designer Goals #1 and #2 should be treated as **premature**. They describe a state that no longer exists. Recommend Orchestrator downgrade those to PROGRESS until re-applied + re-pinned.
