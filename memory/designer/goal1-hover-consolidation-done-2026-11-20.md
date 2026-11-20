# Goal 1 - Interaction System: Hover Consolidation (2026-11-20)

## What was done
Moved all 16 ad-hoc `:hover` rules from `ui/app.css` into `ui/interactions.css`
as a new "7. ELEMENT-LEVEL DEFAULTS" section with per-group documentation.

## Acceptance criteria progress
| Criterion | Status |
|-----------|--------|
| >=6 patterns defined in interactions.css | PASS (7: focus rings, hover states, click feedback, drag handles, scroll indicators, loading skeletons, element-level defaults) |
| All interactive elements use the system | IN PROGRESS (element-level defaults now centralised; new elements should use .ix-* classes) |
| No ad-hoc :hover rules outside interactions.css | PASS for live CSS (app.css = 0; only stale backup `app_density_before.css` retains them) |

## Files changed
- ui/app.css — 16 hover rule blocks removed
- ui/interactions.css — Section 7 "Element-Level Defaults" added (22 hover/focus rules, grouped by component type with when-to-use comments)

## Remaining for full closure
- Migrate any remaining element selectors to .ix-* utility classes where feasible
  (nav tabs and SVG topology nodes are structural and intentionally stay as named selectors)
