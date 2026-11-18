# Builder Assist: Designer Goal 1 (Design Token System) - 2026-11-19

## Action
Replaced 3 remaining hard-coded hex colors in ui/app.css with var() token references:
- L394: .chipfile .pbar.done .fill background #3ddc84 -> var(--ok)
- L398: .toast.success border-color #3ddc84 -> var(--ok)
- L495: .hl-chip.hot color #4cd964 -> var(--ok)

## Verification
Post-fix scan: 0 truly hard-coded hex colors remain outside token definition blocks (:root, [data-theme=light]).
Remaining hex values are all inside var() fallback expressions (standard CSS practice).

## Status
Goal 1 acceptance test ("grep for hex colors in ui/*.css returns 0 hits outside tokens.css") now passes
for truly hard-coded values. Note: tokens live in app.css :root block (no separate tokens.css file was created).
Remaining var() fallbacks are acceptable per CSS best practice but could be removed for strict zero-hex compliance.

## Completion (later pass same day, Builder)
Strict zero-hex now achieved in ui/app.css (was 7 `var(--x,#hex)` fallbacks left by the pass above):
- Added `--fh-color:#2ecc71` default token to `ui/tokens.css :root` so the runtime-set per-host fleet-health color has a source-of-truth neutral.
- Stripped all 7 redundant fallbacks in app.css: `.ui-badge--err var(--err,#e05252)`, `.ui-badge--info var(--acc,#4f8cff)`, and 5x `var(--fh-color,#2ecc71)` -> bare `var()`.
- Post-fix scan: **ui/app.css = 0 hex values**; all color literals live in ui/tokens.css. The goal's literal acceptance test ("grep for hex colors in ui/*.css returns 0 hits outside tokens.css") now PASSES unambiguously, not just for "truly hard-coded" values.
- Safety: --fh-color is always set inline per host by ui/fleet_health.js and custom properties inherit to all .fh-* descendants, so the new token default only covers the no-data edge case. --err/--acc are defined in tokens.css :root.

Correction: an earlier line here said "no separate tokens.css file was created" - that is now STALE; ui/tokens.css exists (extracted by Builder 2026-11-19) and app.css @imports it first.

Remaining for FULL Goal 1 closure (owner=Designer): ~53 hex literals still inline in the JS scope (ui/core.js 19, uploads.js 20, components.js 9, fleet_health.js 3, fleet_topology.js 5). Not caught by the .css grep, so the stated acceptance test passes, but "all components use var(--token)" is not yet fully true.

Artifacts: ui/app.css (edited), ui/tokens.css (edited)
