# Evidence: Cycle-2 re-application (pass f, 2026-11-16)

## Context
Mirror clobber #3 removed all cycle-2 additions from ui/app.css and ui/core.js.
Re-applied in a single atomic pass. Files restored to full feature set.

## Re-applied features

### Goal 1: Dark mode + theme toggle
- `[data-theme="light"]` block: 12 color token overrides
- 14 light-mode component rules (acard, msg.you, peek, dmseg, queuePanel, etc.)
- `@media(prefers-color-scheme: light)` fallback for first-visit users
- core.js: IIFE injects `#themeToggle` button; reads/writes localStorage["portal-theme"]
- Sun/moon icon swap (\u2600/\u263e)

### Goal 3: Status indicator system
- `.status-dot` component: 8px circle, flex:none, margin-right var(--sp-4)
- State modifiers: .ok/.idle → green, .busy/.warn → amber, .err/.unknown → red, .off → grey

### Goal 4: Focus rings + reduced-motion guard
- Global `:focus-visible`: 2px solid var(--focus), 2px offset on all interactive elements
- `@media(prefers-reduced-motion:reduce)`: forces all transitions/animations to .001ms

### Goal 8: Typography hierarchy pass
- h1 font-weight 600→700 (3 steps: 400/600/700)
- #actBody line-height 1.7→1.5 (within 1.2–1.6 range)
- letter-spacing .06em on uppercase labels (.ah, #queueHead)

### Goal 10: Design QA regression gate
- design_check.py: PASS, 0 hard violations

## Final file sizes
- ui/app.css: 18,615 → 21,014 bytes (+2,399)
- ui/core.js: 28,641 → 29,929 bytes (+1,288)

## Verification
- CSS brace balance: OK (225/225) ✓
- design_check.py exit 0 ✓
- All 7 hard checks pass ✓
