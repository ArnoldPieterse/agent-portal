# Color Token Completeness Fix - 2026-11-23

## Context
Auto-loop contribution pass (Designer at 10/10, assisting team). Ran a production
CSS color audit across all loaded files to verify token discipline.

## Finding
app.css L57 (.roundend.warn) used hardcoded rgba(255,159,67,...) values - the
dark-theme warn hex baked in. In light mode (--warn: #c47a12), the background and
border would not match the theme's actual warn color.

All other "hardcoded colors" in production CSS are either:
- Token definitions (tokens.css itself)
- Fallback values in var() syntax: var(--name, #fallback) - defensive, not violations
- Functional overlay/shadow rgba(0,0,0,...) - theme-independent by design

## Fix
1. tokens.css: Added --warn-soft + --warn-line to dark :root block (matching the
   existing pattern of --ok-soft/--ok-line). Also added [data-theme=light] overrides
   for both ok and warn soft/line tokens so they adapt per theme.

2. app.css L57: .roundend.warn now uses var(--warn-soft) and var(--warn-line),
   consistent with .roundend.ok which already used var() tokens.

## Files Changed
- ui/tokens.css (4 lines added: 2 dark + 2 light token definitions)
- ui/app.css (1 line changed: L57 hardcoded rgba replaced with var() references)

## Verification
Post-fix audit: 0 remaining theme-dependent color violations in app.css.
The warn/ok roundend classes are now symmetric in token usage.
