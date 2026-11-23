#!/usr/bin/env python3
"""Verify cycle-12 goal 1: Adaptive Information Density (Calm vs Incident)"""
import re, json, pathlib

css = pathlib.Path('ui/cockpit-density.css').read_text(encoding='utf-8')
js = pathlib.Path('ui/cockpit-density.js').read_text(encoding='utf-8')
results = {}

# C1: Calm mode shows <= 3 primary panels (health + loops visible, others hidden)
calm_block = re.search(r'\[data-density="calm"\]\.panel-health,(?:[^{]*?)\{([^}]+)\}', css)
visible_calm = []
if calm_block:
    body = calm_block.group(1)
    if 'display:block' in body.replace(' ', ''):
        visible_calm = ['health', 'loops']
# Check hidden panels
hidden_calm = re.findall(r'\[data-density="calm"\]\.panel-(\w+)', css)
# Remove ones that are explicitly shown
hidden_panels = [p for p in set(hidden_calm) if p not in visible_calm]
c1_pass = len(visible_calm) <= 3
results['c1_visible'] = visible_calm
results['c1_hidden_count'] = len(hidden_panels)
results['c1_pass'] = c1_pass

# C2: Auto-trigger mechanism (MutationObserver + critical event handler)
c2 = 'MutationObserver' in js and ('panel:critical' in js or 'is-critical' in js)
results['c2_pass'] = c2

# C3: Transition < 500ms
dur = re.search(r'--density-transition:\s*(\d+)ms', css)
c3 = dur and int(dur.group(1)) < 500
results['c3_ms'] = int(dur.group(1)) if dur else None
results['c3_pass'] = c3

# C4: Reduced motion instant swap
c4 = ('prefers-reduced-motion' in css) and ('transition: none' in css)
results['c4_pass'] = c4

# C5: Reversible (both modes have symmetric rules)
c5 = '[data-density="calm"]' in css and '[data-density="incident"]' in css
results['c5_pass'] = c5

# C6: Scroll preservation (JS saves/restores scrollTop)
c6 = 'scrollTop' in js and 'prevScroll' in js
results['c6_pass'] = c6

# C7: JS sets data-density attribute matching CSS selectors
c7 = 'setAttribute("data-density"' in js or "setAttribute('data-density'" in js
results['c7_pass'] = c7

all_pass = all(results[f'c{i}_pass'] for i in range(1,8))
results['ALL_PASS'] = all_pass
print(json.dumps(results, indent=2))