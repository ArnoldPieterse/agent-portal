# Goal 7 - Light-theme contrast fix (2026-11-20)

**Problem:** 30 WCAG AA failures in light theme. Root cause: `--muted` and `--warn-text` had no light override (inherited dark-family values), and `--ok`, `--warn`, `--err`, `--faint` were set too bright for white/near-white surfaces.

**Fix (ui/tokens.css, [data-theme=light] block):**
| token | old | new | contrast vs #fff |
|---|---|---|---|
| --ok | #1f9d5b | #1a7a48 | 5.36:1 |
| --warn | #c47a12 | #9c5e0d | 5.22:1 |
| --err | #d64545 | #b93c3c | 5.56:1 |
| --faint | #7a8699 | #5f6d80 | 5.27:1 |
| --muted | (inherited #8b93a7) | #5a6a7e | 5.53:1 |
| --warn-text | (inherited #e3b341) | #92400e | 7.09:1 |

**Verified:** `python memory/designer/contrast_audit.py` → 0 failures, both themes.
