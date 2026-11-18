#!/usr/bin/env python3
"""H1 .frow collision fix - idempotent re-apply for index.html.
State: applied in shared index.html 2026-11-15 ~12:44 (mtime 12:43:55).
If the 5-min mirror reverts index.html to the 10:42 baseline, run this once.
"""
import sys
p = 'index.html'
s = open(p, encoding='utf-8').read()
if '.ffrow{display:flex' in s and s.count('class="ffrow"') == 6:
    print("H1 already applied - nothing to do"); sys.exit(0)
if '.ffrow{display:flex' in s:
    print("PARTIAL state - inspect manually"); sys.exit(1)
a = s.replace('.frow{display:flex;gap:10px}.frow>div{flex:1}',
              '.ffrow{display:flex;gap:10px}.ffrow>div{flex:1}', 1)
b = a.replace('.frow{padding:7px 0;border-bottom:1px dashed var(--line);font-size:12.5px}',
              '.frow{display:flex;gap:10px;padding:7px 0;border-bottom:1px dashed var(--line);font-size:12.5px}', 1)
lines = b.splitlines(keepends=True)
n = 0
for i, l in enumerate(lines):
    if l.strip() == '<div class="frow">':
        lines[i] = l.replace('class="frow"', 'class="ffrow"'); n += 1
assert n == 6, f"expected 6 dialog rows, got {n}"
open(p, 'w', encoding='utf-8').write(''.join(lines))
print(f"H1 applied: 2 css rules + {n} dialog rows")
