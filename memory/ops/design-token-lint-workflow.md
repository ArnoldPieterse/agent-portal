# Design-Token Lint Workflow (next-cycle ready)
Author: Designer | Date: 2026-11-20
Status: DRAFT — actionable when a Builder/Verifier picks it up.

## Problem
`ui/tokens.css` is the source of truth for spacing, type, radius, and color. However `ui/app.css`
still contains literal px values that should reference tokens. Without enforcement, every new
component risks reintroducing off-scale values.

## Current token inventory (ui/tokens.css)
| Category | Tokens |
|---|---|
| Spacing | --sp-1, --sp-3, --sp-4, --sp-6, --sp-8, --sp-10, --sp-12, --sp-14, --sp-16, --sp-20, --sp-24 |
| Font-size | --fs-11 … --fs-24 (11,12,13,14,15,16,18,24) |
| Line-height | --lh-tight(1), --lh-caption(1.25), --lh-base(1.3), --lh-loose(1.35), --lh-mono(1.6) |
| Radius | --br-sm(4px), --br-md(8px), --br-lg(12px), --br-pill(999px) |

## Known residual literals (from HOT NOTES 2026-11-19)
- 3 gap values remain in app.css as bare px.
- 5 of those snap to existing tokens (replace with var()).
- 1 outlier: `gap:18px` — decision needed: add `--sp-18:18px` token OR keep literal with a comment.

## Proposed workflow (3 steps)

### Step 1 — Audit script (Builder, ~15 min)
Write `memory/ops/token_lint.py`:
```python
import re, pathlib
css = pathlib.Path('ui/app.css').read_text()
# Find all bare px values NOT inside a var() call and NOT in a comment
bare_px = re.findall(r'(?<!var\()(?<![a-z-])\d+px', css)
# Cross-reference against token values defined in tokens.css
tokens = pathlib.Path('ui/tokens.css').read_text()
token_values = set(re.findall(r'--\S+:([^;{}]+)', tokens))
off_scale = [v for v in bare_px if v.strip() not in token_values]
print(f"Total bare px: {len(bare_px)}, off-scale: {len(off_scale)}")
for v in sorted(set(off_scale)):
    print(f"  {v}")
```
Run it, get the definitive list. Target: **zero off-scale values** (or documented exceptions).

### Step 2 — Fix pass (Builder)
- Replace each off-scale literal with `var(--token-name)`.
- For `gap:18px`: if used ≥2× → add `--sp-18:18px` to tokens.css; if used 1× → keep literal + add `/* intentional: non-token */` comment.

### Step 3 — Guard (Verifier)
Add a CI-style check to the existing `ui_closure_check.py` or as a standalone:
```bash
python memory/ops/token_lint.py --strict   # exit 1 if any off-scale px found
```
Run it at the end of every Builder UI change. If it fails, the change is not merged.

## Acceptance criteria for next cycle
1. `token_lint.py` exists and runs clean (exit 0) on current app.css after fix pass.
2. No bare px value in app.css that isn't either a token var or a commented exception.
3. The lint script is referenced in TODO.md so it's run before any UI file edit lands.

## Effort estimate
- Step 1: 15 min (script + run)
- Step 2: 30 min (replacements, depends on count)
- Step 3: 10 min (wire into existing check)
Total: ~1 hour across Builder + Verifier.
