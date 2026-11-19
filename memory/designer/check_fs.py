import os, re
base = os.path.dirname(os.path.abspath(__file__))
root = os.path.join(base, '..', '..')

# 1. Basic balance check on edited files
for fname in ['ui/core.js', 'ui/uploads.js']:
    fpath = os.path.join(root, fname)
    with open(fpath, encoding='utf-8') as f:
        content = f.read()
    # Count braces/parens (rough - ignores strings but good enough for sanity)
    ob, cb = content.count('{'), content.count('}')
    op, cp = content.count('('), content.count(')')
    status = 'OK' if (ob==cb and op==cp) else f'MISMATCH braces {ob}/{cb} parens {op}/{cp}'
    print(f'{fname}: {status}')

# 2. Re-scan for non-ASCII symbols
files_to_check = ['index.html', 'ui/core.js', 'ui/uploads.js', 'ui/tour.js', 'ui/notifications.js',
                  'ui/icons.js', 'ui/fleet_health.js', 'ui/fleet_status.js', 'ui/fleet_topology.js',
                  'ui/components.js', 'ui/fleet_goals_bars.js']
total = 0
for fname in files_to_check:
    fpath = os.path.join(root, fname)
    if not os.path.exists(fpath): continue
    with open(fpath, encoding='utf-8') as f:
        content = f.read()
    for i, line in enumerate(content.split('\n'), 1):
        for m in re.finditer(r'[\U0001F300-\U0001FAFF\u2600-\u27BF\u2190-\u21FF\u2B00-\u2BFF]', line):
            pos = m.start()
            prefix = line[max(0,pos-2):pos]
            if prefix.endswith('\\u') or prefix.endswith('\\U'): continue
            total += 1
            print(f'  {fname} L{i}: U+{ord(m.group()):04X} ctx={line[max(0,m.start()-30):m.end()+20].strip()[:70]}')
print(f'\nRemaining non-ASCII symbols: {total}')
