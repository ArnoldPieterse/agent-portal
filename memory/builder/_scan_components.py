import glob, re
for f in ['index.html'] + sorted(glob.glob('ui/*.js')):
    s = open(f, encoding='utf-8').read()
    hits = {k: len(re.findall(r'\b' + re.escape(k) + r'\s*\(', s)) for k in
            ['UI.card', 'UI.badge', 'UI.gauge', 'UI.timelineNode', 'UI.collapsiblePanel']}
    if any(hits.values()) or 'components.js' in s:
        print(f, hits)
print('scan done')
