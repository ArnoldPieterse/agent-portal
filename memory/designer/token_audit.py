#!/usr/bin/env python
# Goal #1 verification: every hardcoded color/radius in ui/app.css component rules replaced by var(--token).
# Strips the three token-definition blocks (by brace-matching) then greps what remains.
import re, sys
css = open('ui/app.css', encoding='utf-8').read()

def strip_block(s, sel):
    i = s.find(sel)
    if i < 0:
        return s
    j = s.find('{', i); d = 0; k = j
    while k < len(s):
        if s[k] == '{': d += 1
        elif s[k] == '}':
            d -= 1
            if d == 0: break
        k += 1
    return s[:i] + s[k+1:]

for sel in [':root{', '[data-theme="dark"]{', '@media(prefers-color-scheme:dark){']:
    css = strip_block(css, sel)

tokens_total = len(re.findall(r'--[\w-]+\s*:', open('ui/app.css', encoding='utf-8').read()))
if '--list' in sys.argv:
    for i,l in enumerate(css.split(chr(10))):
        if re.search(r'#[0-9a-fA-F]{3,6}\b|rgba?\(',l): print(l.strip()[:85])
    sys.exit(0)
hard_col = sum(len(re.findall(r'#[0-9a-fA-F]{3,6}\b|rgba?\(', l)) for l in css.split(chr(10)))
hard_rad = len(re.findall(r'border-radius:\s*\d+px', css))
print(f'tokens_defined={tokens_total} hardcoded_colors_in_rules={hard_col} hardcoded_px_radii={hard_rad}')
sys.exit(0 if hard_col == 0 and hard_rad == 0 else 1)
