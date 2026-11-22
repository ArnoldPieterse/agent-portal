# Portal UI Change Checklist (Designer, 2026-11-23)

Purpose: any agent modifying `index.html`, `ui/app.css`, `ui/tokens.css`, `ui/core.js`, or `ui/uploads.js` follows this to avoid the clobber loop and token-cycle bugs.

## Before editing
1. Read `memory/portal/INDEX.md` for current pin state.
2. Confirm which file is pinned (`index.html` per PIN_FILES in memory_mirror.py).
3. Check that your change doesn't introduce a `var()` alias inside `[data-theme=light]` (cycle = all tokens invalid at computed-value time).

## Design conventions (source of truth: ui/tokens.css)
- **Spacing**: use only `--sp-*` vars (1, 3, 4, 6, 8, 10, 12, 14, 16, 20, 24). No raw pixel values.
- **Radius**: `--br-sm`(4), `--br-md`(8), `--br-lg`(12), `--br-pill`(999).
- **Font sizes**: `--fs-11` through `--fs-24`. Body = 14, captions/labels = 12.
- **Colors**: never hardcode hex outside tokens.css. Use semantic vars (`--acc`, `--ok`, `--warn`, `--err`, `--dim`, `--faint`).
- **Light theme**: literal values only in `[data-theme=light]` block. Dark is `:root` default.
- **Components**: panels get `background:var(--panel)` + `border-bottom:1px solid var(--line)`; cards get `--panel2` + `--br-md`; buttons get `--btn` class or inline with `border-radius:var(--br-md)`, `font-size:var(--fs-12/14)`.

## After editing (pin advance for index.html)
1. Compute sha12: `python -c "import hashlib;print(hashlib.sha1(open('index.html','rb').read()).hexdigest()[:12])"`
2. Copy to backup: `memory/designer/index_html_CANONICAL_<sha12>_YYYY-MM-DDx.html`
3. Update `PIN_FILES` dict in `memory_mirror.py` with new sha12 + backup path.
4. Commit all changes.
5. **Do NOT skip step 3** — the mirror cycle will revert index.html to the old pin otherwise (clobber loop).

## Non-pinned files (ui/*.css, ui/*.js)
No pin procedure needed; just edit and commit. The mirror syncs them normally.

## Quick reference: token groups
| Group | Tokens |
|-------|--------|
| Surfaces | `--bg`, `--panel`, `--panel2`, `--line` |
| Text | `--text`, `--dim`, `--faint`, `--muted` |
| Accent/State | `--acc`, `--ok`, `--warn`, `--err`, `--focus` |
| Message | `--msg-you`, `--msg-you-bd`, `--sel-bg` |
| DM | `--dm-border`, `--dm-text`, `--dm-bg` |
| Fleet dots | `--dot-idle`, `--dot-busy`, `--dot-err` |
| Print | `--print-dim`, `--print-line`, `--print-border` |

## Anti-patterns (seen in past reverts)
- Adding a new token in app.css instead of tokens.css → gets lost on re-land.
- Using `var(--x)` inside `[data-theme=light]` where `--x` is also overridden there → circular reference, browser returns initial value.
- Forgetting the pin advance after index.html edit → next mirror cycle silently reverts it.

---
*Evidence: memory/designer/ui-change-checklist-2026-11-23.md (this file)*