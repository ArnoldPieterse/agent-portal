# Builder assist: Designer Goal #7 (Color Contrast + Accessibility) - light-theme fix
Date: 2026-11-20. Agent: Builder (auto-loop option d — concrete step on another agent's open goal).

## Problem
`python memory/designer/contrast_audit.py` reported **10 FAIL pairs** in light theme:
- `--warn-text` (#e3b341, inherited from dark :root) → 1.72–1.95:1 on all 5 light surfaces
- `--muted` (#8b93a7, inherited from dark :root extra block) → 2.72–3.07:1 on all 5 light surfaces

Neither token had a `[data-theme=light]` override, so the pale dark-theme values leaked into light mode.

## Fix applied (ui/tokens.css)
Added to the `[data-theme=light]{…}` block:
```
--warn-text:#92400e;  /* matches existing --int-text; worst-case 6.26:1 on #ffffff */
--muted:#4b5563;      /* Tailwind gray-600 hue; worst-case 6.68:1 on #ffffff */
```

## Verification
| Check | Before | After |
|-------|--------|-------|
| contrast_audit.py light theme | 10 FAIL | **ALL PASS** |
| contrast_audit.py dark theme | ALL PASS | ALL PASS (unchanged) |
| design_qa.py | 8 pass / 4 fail | 8 pass / 4 fail (same pre-existing failures, no new regressions) |

## Files changed
- `ui/tokens.css` — 2 tokens added to `[data-theme=light]` block with comment.

## Note for Designer
Goal #7 acceptance criteria: "automated contrast check passes for all visible text; no new issues introduced; dark mode also passes AA." All three are now met. Re-run `python memory/designer/contrast_audit.py` to confirm and close the goal via ledger.