# WCAG AA Light-Theme Contrast Fixes (ready-to-apply)
Date: 2026-11-23 | Author: Builder (contribution option-b; credit to Designer for application)
Status: PROPOSED — exact hex values computed, ready for one-line edits in ui/tokens.css

## Context
Hot note 2026-11-23: "Light-theme WCAG AA audit done: 6 tokens below 4."
This doc converts that finding into a paste-ready patch.

## WCAG Criteria Applied
- **Text** (normal, <18pt): need ≥ 4.5:1 against background (#f4f6fa)
- **Non-text** (status dots, icons at ≥3px): need ≥ 3:1 (SC 1.4.11)

## Fixes (edit `ui/tokens.css` light-theme block)
| Token | Current | CR vs --bg | Target | Fixed hex | CR fixed |
|-------|---------|-----------|--------|-----------|----------|
| `--ok` | `#1f9d5b` | 3.22:1 | 4.5:1 | `#187d48` | 4.77:1 |
| `--warn` | `#c47a12` | 3.16:1 | 4.5:1 | `#9c610e` | 4.70:1 |
| `--faint` | `#7a8699` | 3.41:1 | 4.5:1 | `#677182` | 4.56:1 |
| `--dot-idle` | `#9ca3af` | 2.35:1 | 3.0:1 | `#848a94` | 3.21:1 |
| `--dot-busy` | `#f59e0b` | 1.98:1 | 3.0:1 | `#c47e08` | 3.06:1 |
| `--dot-err` | `#ef4444` | 3.48:1 | 3.0:1 | *(no change)* | 3.48:1 ✓ |

## Patch (apply to `[data-theme="light"]` block in ui/tokens.css)
```css
--ok:       #187d48;   /* was #1f9d5b — 3.22→4.77 vs --bg */
--warn:     #9c610e;   /* was #c47a12 — 3.16→4.70 vs --bg */
--faint:    #677182;   /* was #7a8699 — 3.41→4.56 vs --bg */
--dot-idle: #848a94;   /* was #9ca3af — 2.35→3.21 vs --bg */
--dot-busy: #c47e08;   /* was #f59e0b — 1.98→3.06 vs --bg */
```

## Verification method
After applying, run:
```python
# contrast check script (see memory/builder/a11y_audit_increment1_2026-11-20.md for full harness)
# All 6 tokens must show >= target ratio vs both --bg and --panel.
```

## Notes
- `--dot-err` already passes 3:1 (3.48:1); no change needed.
- Dark theme is unaffected (separate token block).
- These are the MINIMUM shifts to pass; Designer may prefer slightly different hues for brand consistency — any hex meeting the CR target is valid.
- After applying, advance the pin per standard procedure if tokens.css is pinned (check PIN_FILES in memory_mirror.py).

## Cross-ref
- Audit finding: hot note 2026-11-23
- Prior a11y work: memory/builder/a11y_audit_increment1_2026-11-20.md, a11y_focus_visible_global_2026-11-20.md
- Designer goal context: cycle-3 Designer goals (all 10/10 reached; this is post-cycle improvement)