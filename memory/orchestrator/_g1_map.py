"""One-off: classify Designer goal-1 component hexes (brace-accurate)."""
import re, json, io
css = io.open('ui/app.css', encoding='utf-8').read()
dark, light = {}, {}
def grab(block):
    out = {}
    for m in re.finditer(r'([\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8})', block):
        out[m.group(1).lower()] = m.group(2).lower()
    return out
i = css.find(':root{')
dark = grab(css[i:css.find('}', i)])
j = css.find('[data-theme=light]{')
light = grab(css[j:css.find('}', j)])
# brace-depth component hexes
blocks, depth, cur = [], 0, None
for m in re.finditer(r'([{}])|(:root\s*\{|\[data-theme[^\]]*\]\s*\{)', css):
    if m.group(2):
        if cur is None:
            cur = m.start()
        depth += 1
    elif m.group(1) == '{':
        depth += 1
    else:
        depth -= 1
        if depth == 0 and cur is not None:
            blocks.append((cur, m.end())); cur = None
comp = [(m.start(), m.group(0).lower()) for m in re.finditer(r'#[0-9a-fA-F]{3,8}\b', css)
        if all(not (a <= m.start() < b) for a, b in blocks)]
from collections import Counter
cnt = Counter(h for _, h in comp)
def line_at(off):
    return css.count('\n', 0, off) + 1
A, C = {}, {}
for h, n in cnt.items():
    if h in dark.values():
        A[h] = {'n': n, 'token': [k for k, v in dark.items() if v == h], 'line': line_at(next(o for o, x in comp if x == h))}
    else:
        C[h] = {'n': n, 'line': line_at(next(o for o, x in comp if x == h))}
print('TOTAL occurrences:', len(comp), '| unique:', len(cnt))
print('\n=== A: swap to EXISTING dark token (%d) ===' % len(A))
for h, d in sorted(A.items(), key=lambda kv: -kv[1]['n']):
    print('  %-9s x%-2d L%-3d -> var(%s)' % (h, d['n'], d['line'], ','.join('--'+t for t in d['token'])))
print('\n=== C: needs NEW token / sub-palette (%d) ===' % len(C))
for h, d in sorted(C.items(), key=lambda kv: -kv[1]['n']):
    print('  %-9s x%-2d L%d' % (h, d['n'], d['line']))
io.open('memory/orchestrator/_designer_goal1_hexmap.json', 'w').write(
    json.dumps({'total_occurrences': len(comp), 'unique': len(cnt),
                'swap_to_existing': A, 'needs_new_token': C}, indent=2))
print('\nsaved _designer_goal1_hexmap.json')