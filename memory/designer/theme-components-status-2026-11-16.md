# Evidence: Theme tokens + Component abstractions + Status dot (2026-11-16)

## Goals addressed
- **Goal 1** (Dark mode + theme toggle): `[data-theme="light"]` token override block added to ui/app.css (14 light-mode rules covering panels, peek, DM segments, queue, banner). JS-injected `#themeToggle` button in core.js IIFE reads/writes `localStorage["portal-theme"]`; defaults to dark; sun/moon icon swap.
- **Goal 2** (Component abstraction): Four named utility classes extracted in app.css: `.panel-head`, `.btn-primary`, `.badge-status`, `.input-bar`. These match the patterns already used by #fleetHead/#opsHead/etc. and can replace id-specific rules in a follow-up refactor.
- **Goal 4** (Status indicator system): Unified `.status-dot` component with state modifiers: `.ok/.idle` (green), `.busy/.warn` (amber), `.err/.unknown` (red), `.off` (grey). Replaces ad-hoc `.dot` and `.fdot` patterns.

## Files changed
- `ui/app.css`: 18,615 → 20,841 bytes (+2,226)
- `ui/core.js`: 28,641 → 29,712 bytes (+1,071)

## Verification
- CSS brace balance: 226/226 ✓
- All new classes present in output ✓
- Theme toggle IIFE + localStorage key present in core.js ✓

## Next steps (not done this pass)
- Migrate existing id-specific rules (#fleetHead, #opsHead, etc.) to use `.panel-head` class — requires index.html pin advance
- Replace inline `.dot`/`.fdot` usages in JS render functions with `.status-dot` + state class
- Wire `prefers-color-scheme: light` as fallback when no localStorage value set
