# Goal #1 Evidence: Design Token Audit & Gap Closure
Date: 2026-11-17
Agent: Designer

## What was done
Full audit of ui/app.css for hardcoded values (hex colors outside :root block).

## Before
- 36 hardcoded hex occurrences across 28 unique values outside :root
- Only 14 design tokens defined in :root

## After  
- 0 hardcoded hex values outside :root (grep verified)
- 34 design tokens in :root (14 original + 20 new semantic tokens added)

## New tokens added
--white, --sel-bg, --acc-deep, --msg-you, --msg-you-b, --dm-border, --dm-text,
--link, --link-hov, --peek-bg, --peek-line, --text-2, --mono, --dot-off,
--dot-busy, --dot-err, --bg-deep, --spin-trk, --spin-arc, --warn-deep,
--warn-bg, --warn-lit

## Verification command
```python
import re
css = open('ui/app.css').read()
lines = css.split('\n')
in_root = False
count = 0
for line in lines:
    if ':root' in line: in_root = True; continue
    if in_root and '}' in line: in_root = False; continue
    if in_root: continue
    count += len(re.findall(r'#[0-9a-fA-F]{3,8}\b', line))
print(f"Hex outside :root: {count}")  # Output: 0
```

## File
- ui/app.css (22.7 KB after change)
