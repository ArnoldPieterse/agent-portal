# Goal 5 progress: line-length constraint (2026-11-20)

## What was done
- Added `--line-max:75ch` token to `ui/tokens.css` (`:root` block, after line-height tokens).
- Applied `max-width:min(78%,var(--line-max))` to `.msg` (chat messages cap at 75ch on wide screens, 78% on narrow).
- Applied `max-width:var(--line-max)` to `.think` (reasoning blocks) and `.dmseg .dmbody` (DM body text).

## Verification
- All font-size declarations in live CSS use `--fs-*` tokens (zero orphaned raw px values).
- Braces balanced 304/304 after edit.
- Monospace containers (`.opsbox`, `#actBody`) intentionally NOT constrained — log/code views need full width.

## Remaining for full closure
- [ ] Document scale ratios in tokens.css header comment (minor).
- [ ] Optional: add `--line-max` to light theme block if it should differ (currently same 75ch both themes — correct, readability is font-size-relative not theme-dependent).
