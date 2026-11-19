import hashlib, os, re

def sha(p):
    try:
        return hashlib.sha1(open(p, 'rb').read()).hexdigest()[:12]
    except Exception as e:
        return 'ERR ' + str(e)

for f in ['ui/core.js', 'ui/app.css', 'ui/icons.js', 'index.html']:
    sz = os.path.getsize(f) if os.path.exists(f) else 'MISSING'
    print('HASH', f, sha(f), sz)

core = open('ui/core.js', encoding='utf-8', errors='replace').read() if os.path.exists('ui/core.js') else ''
css = open('ui/app.css', encoding='utf-8', errors='replace').read() if os.path.exists('ui/app.css') else ''

print('--- GOAL BAR / DATA-VIZ EVIDENCE (live) ---')
print('core.js  <svg count        :', len(re.findall(r'<svg|createElement\([\'"]svg', core, re.I)))
print('core.js  SMIL <animate     :', len(re.findall(r'<animate', core, re.I)))
print('core.js  @keyframes        :', len(re.findall(r'@keyframes', core, re.I)))
print('css      .gbar-fill present:', bool(re.search(r'\.gbar-fill', css)))
print('css      transition on gbar-fill block:', bool(re.search(r'\.gbar-fill\s*\{[^}]*transition', css)) or bool(re.search(r'transition[^;]*;', re.search(r'\.gbar-fill\s*\{.*?\}', css).group(0)) if re.search(r'\.gbar-fill\s*\{.*?\}', css) else False))
print('css      animation on gbar-fill block :', bool(re.search(r'\.gbar-fill\s*\{[^}]*animation', css)))
# show the actual goal bar render function
m = re.search(r'(function\s+renderGoalBar|goalBar|gbar-fill)', core)
print('core.js  goal-bar code found at:', (m.start() if m else 'NONE'))
i = core.find('gbar-fill')
if i >= 0:
    print('CONTEXT:', core[max(0, i-260):i+120].replace('\n', ' '))
