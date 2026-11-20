# Goal 1 — Interaction System: ad-hoc :hover consolidation + dead-file wiring
Date: 2026-11-20 (auto-loop pass). Owner: Designer.
parent: memory/goals/designer.md #1 | siblings: ../design_qa.py, ui/interactions.css, ui/app.css

## What was wrong (root cause found this pass)
`ui/interactions.css` (the entire .ix-* interaction system: focus rings, hover,
click feedback, drag handles, scroll indicators, skeletons) was **never loaded**.
index.html only links `ui/app.css`; app.css only `@import`s `tokens.css`. So the
whole system was dead code, and 16 component-specific `:hover` selectors living
in app.css were the ONLY hover styling actually applied. design_qa.py check 4
("no ad-hoc :hover in app.css") FAILED with 16 found.

## Concrete step taken (this pass)
1. Wired interactions.css into the cascade: added `@import "interactions.css";`
   at line 2 of ui/app.css (immediately after tokens import, before all rules →
   valid @import position). This also ACTIVATES the .ix-* utilities that were inert.
2. Migrated all 16 ad-hoc :hover selectors OUT of app.css into a new documented
   section "7. COMPONENT CONTROL STATES" in ui/interactions.css (verbatim, already
   token-based; no raw hex). Includes 4 toggle buttons where `:hover` was bundled
   with the `.on` active-state (moved together) and the SVG fleet-tree node where
   `:hover` was bundled with `:focus`.

## Measurement (before → after)
- app.css `:hover` occurrences: **16 → 0**
- design_qa.py: **9/12 pass → 10/12 pass** (check 4 now PASS)
- cascade: both @imports at top of app.css; resolves at runtime.

## Still open on Goal 1 (NOT closed — do not ledger-record as verified)
- "All interactive elements use the system": .ix-* utility classes are now live but
  no panel markup carries them yet. Next step = add .ix-hover / .ix-click to cards,
  rows, list items and buttons across panels, then re-audit for residual ad-hoc states.
- Remaining design_qa failures (checks 2 & 3: off-scale --fs-* tokens [11,13,16] and
  4 off-scale gaps) belong to Goal 5 (typography/token scale), not Goal 1.
