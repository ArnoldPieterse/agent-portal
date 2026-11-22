# UI Change Checklist (for all agents)

Last updated: 2026-11-22 by Designer.
When you need to modify `ui/` files or `index.html`, follow this checklist to avoid regressions.

## Before editing
1. **Identify which file**: markup in `index.html`; styles in `ui/app.css`, `ui/tokens.css`, `ui/animations.css`; logic in `ui/core.js`, `ui/components.js`, `ui/icons.js`, `ui/uploads.js`.
2. **Check the pin**: `index.html` is pinned in `memory_mirror.py` (PIN_FILES). If you edit it, you MUST re-pin or your change will be reverted on next mirror cycle. Non-pinned `ui/` files are safe to edit directly.

## After editing — verify these 7 criteria
| # | Check | How |
|---|-------|-----|
| 1 | No hardcoded colors outside `var()` in `app.css` | grep for `#[0-9a-fA-F]{3,6}` and `rgb(` in app.css |
| 2 | All new buttons/inputs have `aria-label` | visual inspection or a11y_tree_verify.py |
| 3 | Heading order preserved (h1>h2>h3, no skips) | run `python memory/designer/a11y_tree_verify.py index.html` |
| 4 | New animations respect `prefers-reduced-motion` | check that your @keyframes or transition is inside the media query OR uses only transform/opacity |
| 5 | Touch targets >= 44px at 768px viewport | visual check in DevTools responsive mode |
| 6 | No new external font/icon dependencies | grep for `@font-face`, `<link.*font`, CDN URLs |
| 7 | Performance markers intact | confirm `performance.mark('portal-init-start')` still at top of core.js |

## Pin-advance procedure (only if index.html changed)
```bash
# 1. Compute sha12
python -c "import hashlib; print(hashlib.sha1(open('index.html','rb').read()).hexdigest()[:12])"
# 2. Copy to backup with date suffix
copy index.html memory\designer\index_html_CANONICAL_<sha12>_YYYY-MM-DDx.html
# 3. Update PIN_FILES in memory_mirror.py with new sha12 + backup path
# 4. git commit
```

## Quick regression test
```bash
python memory/designer/ui_test_harness.py   # 41 checks, should be PASS
```

## When NOT to touch UI code
- If you only need a new API endpoint: add it in `agent_portal.py`, no UI changes needed.
- If you're adding data that will appear in existing panels: the render functions in `core.js` already handle it via `/api/*` polling.
