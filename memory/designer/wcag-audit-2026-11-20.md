# WCAG 2.1 AA Audit — Portal (2026-11-20)
Owner: Designer. Status: **In progress** — contrast leg complete; keyboard + ARIA legs pending.

## 1. Color Contrast (PASS ✓)

### Before fix (2026-11-20, first audit)
`python memory/designer/contrast_audit.py` reported **30 failing pairs** in the light theme:
| Token | Old value | Min ratio | Cause |
|-------|-----------|-----------|-------|
| --warn-text | #e3b341 | 1.72:1 | Dark-theme gold leaking (no light override) |
| --muted | #8b93a7 | 2.72:1 | Dark value; media-query override not applied when JS sets data-theme=light |
| --ok | #1f9d5b | 3.07:1 | Too bright for white surfaces |
| --warn | #c47a12 | 3.02:1 | Amber too light on white |
| --faint | #7a8699 | 3.26:1 | Grey too light |
| --err | #d64545 | 3.87:1 | Red slightly below threshold |

### Fix applied (ui/tokens.css, [data-theme=light] block)
| Token | New value | Min ratio | Method |
|-------|-----------|-----------|--------|
| --warn-text | #92400e | 6.26:1 | Dark amber; matches --int-text (same semantic role) |
| --muted | #5e6d80 | 4.67:1 | Slate grey, passes on all 5 surfaces |
| --faint | #5c6b7a | 4.83:1 | Slightly lighter than --dim for hierarchy |
| --ok | #1a7a4a | 4.72:1 | Darker green |
| --warn | #92400e | 6.26:1 | Same dark amber as warn-text |
| --err | #c62828 | 4.97:1 | Material red-800 |

Also added `--qspin-bd`, `--qspin-top`, `--queue-tx` to the `[data-theme=light]` block (previously only in a `@media (prefers-color-scheme: light)` rule that doesn't fire when JS sets the attribute).

### After fix
```
$ python memory/designer/contrast_audit.py
== DARK (min 4.5:1) ==
  ALL PASS
== LIGHT (min 4.5:1) ==
  ALL PASS
RESULT: 0 failing pair(s)
```

**Verdict: 0 critical contrast failures in both themes.**

## 2. Keyboard Navigation (PENDING)
Previous audit (2026-11-18, `a11y-audit-2026-11-18.md`) found 3 violation categories:
- Missing skip-to-content link → **fixed** (see `goal4-skip-link-region-roles-2026-11-18.md`)
- Focus not visible on some interactive elements → partial fix landed
- Tab order in fleet panel not logical → needs re-check after responsive changes

Next step: re-run full keyboard-only walkthrough with current markup.

## 3. ARIA Labels (PENDING)
Need to verify all buttons/inputs have accessible names. Previous audit found some icon-only
buttons missing `aria-label`. Will scan `index.html` + `ui/core.js` DOM generation for gaps.

---
**Evidence**: `contrast_audit.py` run output above; token diff in `ui/tokens.css` (git log).
**Remaining**: keyboard navigation re-verification + ARIA label completeness scan.