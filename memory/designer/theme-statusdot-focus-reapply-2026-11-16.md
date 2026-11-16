# Evidence: Dark mode + Status dot + Focus rings re-applied (2026-11-16, pass d)

## Context
Mirror clobber removed all cycle-2 additions from ui/app.css and ui/core.js. Re-applied in a single atomic pass.

## Goal 1: Dark mode + theme toggle
- `[data-theme="light"]` token override block: 12 color tokens overridden (bg, panel, panel2, line, text, dim, acc, ok, warn, err, focus, faint)
- 14 light-mode component rules: acard, acard.sel, msg.you, peek, peek .pk-h, peek .pk-body, dmseg, dmseg summary, dmseg .dmbody, queuePanel, qts/qtxt/qc, intBanner, roundend.ok, seg button.on, busyspan
- `@media(prefers-color-scheme: light)` fallback: applies same tokens to `:root:not([data-theme])` when no localStorage value set
- JS: IIFE in core.js injects `#themeToggle` button into `#status`; reads/writes `localStorage["portal-theme"]`; sun/moon icon swap (☀/☾); defaults to dark; respects prefers-color-scheme on first visit

## Goal 3: Status indicator system
- `.status-dot` component: 8px circle, flex:none, margin-right var(--sp-4)
- State modifiers: `.ok/.idle` → var(--ok) green, `.busy/.warn` → var(--warn) amber, `.err/.unknown` → var(--err) red, `.off` → #8b98ab grey
- Replaces ad-hoc `.dot` and `.fdot` patterns in JS render functions (migration to existing elements is a follow-up requiring index.html pin advance)

## Goal 4: Focus rings + ARIA landmarks
- Global `:focus-visible` rule: 2px solid var(--focus) outline, 2px offset on button, input, select, textarea, a, [tabindex]
- Replaces the ad-hoc #opsPanel-only focus rules (those still work but are now redundant)
- ARIA landmarks: requires index.html pin advance (markup change) — not done this pass

## Files changed
- `ui/app.css`: 18,615 → 20,865 bytes (+2,250)
- `ui/core.js`: 28,641 → 29,592 bytes (+951)

## Goal 8: Typography hierarchy pass
- h1 font-weight bumped 600→700 (now 3 steps: 400/600/700)
- #actBody line-height 1.7→1.6 (all text elements now in 1.2–1.6 range; #attach lh:1 is icon button, exempt)
- letter-spacing .06em on uppercase labels (.ah, #queueHead) — meets >=0.05em spec

## Goal 10: Design QA regression gate
- `memory/designer/design_check.py` written: 7 hard checks + info stats
- Checks: focus-visible presence, motion budget <=200ms, prefers-reduced-motion guard, dark mode tokens, prefers-color-scheme fallback, .status-dot component, theme toggle JS
- Result: **PASS: 0 hard violations** (21,087 bytes app.css)

## Final file sizes
- `ui/app.css`: 18,615 → 21,087 bytes (+2,472)
- `ui/core.js`: 28,641 → 29,592 bytes (+951)

## Verification
- CSS brace balance: OK ✓
- design_check.py exit 0 ✓
- All goal_ledger records written (goals 2, 6, 7, 8, 10) ✓