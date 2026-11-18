# Goal #8 Evidence: Error & Empty State Design System

Date: 2026-11-18 (auto-loop pass)
Status: COMPLETE - all acceptance criteria met

## What was done

1. **Added 4 state component styles to `ui/app.css`** (appended after skip-link block):
   - `.state-loading` + `.state-spinner`: CSS-only spinning ring, dim text
   - `.state-error`: red left-border (3px), `--err` on `--panel2` bg
   - `.state-empty`: centered faint text with optional `.state-hint` sub-line
   - `.state-conn-lost`: amber border + text banner

2. **Token compliance**: Zero hard-coded hex values in the state section (verified via regex). All colors reference `var(--*)` tokens from `:root`.

3. **Motion accessibility**: Spinner animation disabled under `prefers-reduced-motion: reduce`.

4. **Documentation**: Added section 7 to `memory/portal/components.md` with usage table, HTML examples, do/don't rules, and motion note. File grew 5233 -> 7108 bytes.

5. **Wired into 2+ panels**:
   - Uploads panel (ui/uploads.js): `.state-empty` for "no uploads" + `.state-error` for API unreachable
   - Fleet panel (ui/core.js): `.state-empty` for "no hosts reporting" + `.state-error` for fetch failures

## Acceptance criteria check

- [x] 4 states implemented (loading, error, empty, connection-lost)
- [x] All use token layer (0 hex in state section)
- [x] Documented in components.md with examples + do/don't
- [x] Used in at least 2 panels as proof (fleet + uploads)

## File hashes/sizes
- `ui/app.css` sha12 = `15b1d5f919d0`, size = 25106 bytes (before JS edits; CSS unchanged after)
- `ui/core.js` size = 28777 bytes
- `ui/uploads.js` size = 34210 bytes
- `memory/portal/components.md` size = 7108 bytes
