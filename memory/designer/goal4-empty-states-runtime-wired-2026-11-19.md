# Goal #4 Evidence: Empty states wired at runtime (2026-11-19)

## What was done this pass
Made all 4 empty states actually functional at runtime by adding a self-contained
`window.UI.emptyState()` bootstrap to ui/core.js (which IS loaded in index.html).
Previously the function lived in ui/icons.js which is NOT in the script tags -
so uploads.js calls would throw ReferenceError.

### Changes to ui/core.js:
1. **UI namespace bootstrap** (~30 lines, IIFE at top): defines `window.UI.emptyState()`
   + `window.UI.icon()` with inline SVG paths for 4 icons (agent, goal, upload, warning).
   No dependency on icons.js or components.js.

2. **Fleet panel empty state**: replaced plain `<div class="hint">no hosts</div>` with
   `UI.emptyState({icon:"agent", title:"No agents online", ...ctaLabel:"Refresh now"})`.

3. **Escalations panel** (new, IIFE at bottom): injects `#escalationsPanel` section
   after ops panel in DOM. Contains empty state: warning icon + "No escalations" +
   "Check status" CTA. Will auto-populate when /api/escalations endpoint ships.

### Coverage (all 4 required states now runtime-wired):
| Panel | Empty State | CTA | Source |
|-------|------------|-----|--------|
| Fleet (#fleetBody) | No agents online | Refresh now | core.js fleetUpdate() |
| Goals (#goalsBody) | No goals set | Open TODO.md | uploads.js goalsLoad() |
| Files (#filesList) | No uploads yet | + Upload | uploads.js filesLoad() |
| Escalations (#escBody) | No escalations | Check status | core.js IIFE (new) |

### Verification:
- Brace balance: 243/243 [OK]
- Paren balance: 835/835 [OK]
- CSS: all 5 .empty-state* rules present in app.css with token-based values [OK]
- UI.emptyState available before uploads.js executes (core.js loads first per index.html) [OK]
- Escalations panel injected into DOM without index.html edit (pin-safe) [OK]

### Files changed:
- ui/core.js: +47 lines (UI bootstrap at top, fleet empty state in fleetUpdate, escalations IIFE at bottom)

### Remaining for full acceptance:
- [ ] Live browser CDP screenshot showing all 4 panels with empty states rendered
- [ ] /api/escalations endpoint (scope dependency - not a design gap)
