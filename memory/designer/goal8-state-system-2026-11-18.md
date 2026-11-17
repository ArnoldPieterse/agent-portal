# Goal #8 Error & Empty State Design System — Evidence (2026-11-18)

## What was done this pass
1. **Documented all 4 states** in `memory/portal/components.md` (new section 7):
   - Loading spinner (`.fleet-loading`) — CSS-only border-top spinner, 0.6s linear
   - Error message (`.fleet-error`) — red text + retry button pattern
   - Empty list (`.fleet-empty`) — centered muted guidance with optional SVG icon
   - Connection lost — variant of `.fleet-error` or `.ft-banner-error`
   Each has do/don't examples.

2. **Wired states into 2nd panel** (Goals): `goalsLoad()` in ui/uploads.js now shows:
   - Loading state on fetch start
   - Error state with retry button on API failure or exception
   - Empty state when agents array is empty

3. **AA contrast fix** (bonus for goal #6): added `--acc-deep:#2563eb` token to :root;
   changed `#send` and `.btn.pri` fill from `var(--acc)` (3.22:1) to `var(--acc-deep)` (5.17:1).

## File state
- ui/app.css: 25,036 bytes, sha12=7519c1398a44
- ui/uploads.js: 34,779 bytes, sha12=d77d3e9d6607
- memory/portal/components.md: section 7 added (state patterns)

## Acceptance criteria
- [x] 4 states implemented in CSS with token-based colors/sizes
- [x] Documented in components.md with do/don't examples
- [x] Used in at least 2 panels: Fleet (core.js) + Goals (uploads.js)
- [x] All colors use var() tokens (no hardcoded hex in state classes)
- [x] Motion covered by prefers-reduced-motion block
