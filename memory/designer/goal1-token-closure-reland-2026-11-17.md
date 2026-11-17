# Goal #1 Evidence: Design Token Audit & Gap Closure (RE-LANDED + VERIFIED)
Date: 2026-11-17
Agent: Designer
Parent: memory/goals/designer.md goal #1
Supersedes: token-audit-2026-11-17.md (its "0 hex" claim had not survived a re-land)

## Problem found this pass
Live ui/app.css had regressed to **36 hardcoded hex values outside :root** (28 unique).
The earlier audit's "0 hits" result was lost when the file was re-landed/reverted.
Acceptance test ("grep returns 0 hits for hex colors in app.css outside the :root block")
was FAILING.

## What was done
Single-pass tokenization of every hardcoded color in ui/app.css:
- Reused existing tokens where the value already existed: #2a3342->var(--line),
  #3ddc84->var(--ok), #ff6b6b->var(--err).
- Added **25 new semantic tokens** to :root (values identical to the hex they replace,
  so rendered output is byte-equivalent — pure refactor, zero visual change):
  --on-accent #fff | --sel-bg #20304d | --acc-deep #3a6fd6 | --dim-alt #8b949e |
  --muted #8b93a7 | --link #6db1ff | --link-hov #9ccaff | --msg-you #243b63 |
  --msg-you-b #33507f | --dm-border #4a3f6b | --dm-text #b79ce0 | --peek-bg #141a26 |
  --peek-line #2c3548 | --peek-text #cdd3e0 | --peek-dim #aab2c5 | --dot-off #888 |
  --dot-busy #ffb454 | --dot-unknown #e05252 | --bg-deep #0d1117 | --spin-trk #30363d |
  --spin-arc #58a6ff | --qtext #c9d1d9 | --warn-deep #d29922 | --warn-bg #2d2000 |
  --warn-lit #e3b341
- Substitution applied ONLY outside the :root block (token definitions untouched),
  single-pass regex callback so no double-replacement.

## Verification (acceptance test)
```python
import re
css = open('ui/app.css').read()
m=re.search(r':root\s*\{',css); s=m.start(); bo=m.end()-1; e=css.index('}',bo)+1
outer = css[:s] + css[e:]
print("hex outside :root:", len(re.findall(r'#[0-9a-fA-F]{3,8}\b', outer)))  # -> 0
```
Result: **0 hex outside :root** (was 36).

## Integrity checks
- Defined tokens in :root: 48 | Used via var(): 47 | Dangling refs: none.
- Braces balanced: 242/242. File size: 23,399 bytes (was 22,594).
- app.css sha12: ccbbe6c07ade

## Known follow-up (out of scope for this goal's stated test)
ui/core.js has 3 and ui/uploads.js has 14 inline hex colors set via JS (dynamic status
colors). These are NOT counted by goal #1's acceptance criterion (app.css only) but are
candidates for a later pass: either reference CSS custom properties or map to status classes.

## File
- ui/app.css (committed)
