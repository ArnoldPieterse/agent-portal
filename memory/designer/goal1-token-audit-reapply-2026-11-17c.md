# Goal 1: Design Token Audit & Gap Closure - COMPLETE (re-applied)

Date: 2026-11-17 (auto-loop pass, re-application after revert)

## What was done
Previous token work was reverted by mirror cycle. Re-applied all changes:

### ui/app.css
- Added 28 new CSS custom properties to :root block (total now 42 tokens)
- Replaced all 36 hardcoded hex values with var() references
- Final state: **0 hex colors outside :root** (grep verified)
- Brace balance: 242/242 [PASS]
- File size: 22.9 KB

### ui/core.js
- Added `const T={...}` token mirror object at top
- Replaced all hardcoded hex with T.xxx or var() references
- Final state: **0 hex colors** [PASS]

### ui/uploads.js
- Added `const T={...}` token mirror object (10 tokens)
- Replaced all style assignments with T.xxx / var() references
- 1 remaining hex: triple-fallback in form field default (`getComputedStyle(...).getPropertyValue("--ok")||"#3ddc84"`) - intentional last-resort for non-CSS-var browsers

## New tokens added to :root
--white, --bg-deep, --peek-bg, --card-sel-bg, --msg-you-bg, --peek-border,
--banner-warn-bg, --spin-track, --msg-you-border, --seg-on, --dm-border,
--spin-active, --link, --dot-idle, --text-muted, --queue-text, --link-hover,
--peek-text, --dm-accent, --queue-body, --peek-title, --banner-warn-border,
--dot-err, --banner-warn-text, --dot-busy, --neutral, --agent-purple, --gate-warn

## Verification commands
```python
# app.css: 0 hex outside :root
import re,pathlib;css=pathlib.Path("ui/app.css").read_text()
in_r=False;c=0
for l in css.split('\n'):
    if ':root' in l and '{' in l: in_r=True;continue
    if in_r and '}' in l: in_r=False;continue
    if in_r: continue
    c+=len(re.findall(r'#[0-9a-fA-F]{3,8}\b',l))
assert c==0

# core.js: 0 hex
import re,pathlib
assert len(re.findall(r'#[0-9a-fA-F]{3,8}',pathlib.Path("ui/core.js").read_text()))==0
```

## Artifacts
- ui/app.css (edited in place)
- ui/core.js (edited in place)
- ui/uploads.js (edited in place)
