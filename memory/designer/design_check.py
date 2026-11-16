#!/usr/bin/env python3
"""Design QA regression gate (Goal 10, Designer).
Greps ui/app.css for hard violations: missing focus styles, motion budget,
dark mode tokens, status component. Reports informational token-usage stats.
Run: python memory/designer/design_check.py
Exit 0 = pass (no hard violations), Exit 1 = hard violations found."""
import re, sys, os

css_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'app.css')
css = open(css_path, encoding='utf-8').read()
hard = []   # blocking violations
info = []    # informational (token migration progress)

# --- HARD CHECKS ---

# 1. Focus rings: :focus-visible rule must exist
if ':focus-visible' not in css:
    hard.append("NO :focus-visible rule - focus rings missing")
else:
    ring_count = len(re.findall(r':focus-visible', css))
    info.append(f"focus-visible rules: {ring_count}")

# 2. Motion budget: non-exempt transitions <=200ms
transitions = re.findall(r'(?:transition|animation)[^;]*?([\d.]+)s', css)
exempted = []
for t in transitions:
    if float(t) > 0.2:
        # Find context to check exemption (qspin, pulse)
        pos = css.find(t + 's')
        ctx = css[max(0,pos-100):pos]
        if 'qspin' in ctx or 'pulse' in ctx:
            continue
        exempted.append(f"{t}s")
if exempted:
    hard.append(f"motion budget exceeded: {exempted}")
else:
    info.append(f"motion budget OK (max non-exempt <= 200ms)")

# 3. prefers-reduced-motion guard
if 'prefers-reduced-motion' not in css:
    hard.append("NO @media(prefers-reduced-motion) guard")
else:
    info.append("prefers-reduced-motion guard present")

# 4. Dark mode token block
if '[data-theme="light"]' not in css:
    hard.append("[data-theme=\"light\"] token override block missing")
else:
    light_tokens = re.findall(r'--\w+:[^;]+', css[css.find('[data-theme="light"]'):])
    info.append(f"dark mode: [data-theme=light] present ({len(light_tokens)} token overrides)")

# 5. prefers-color-scheme fallback
if 'prefers-color-scheme' not in css:
    hard.append("NO @media(prefers-color-scheme) fallback")
else:
    info.append("prefers-color-scheme fallback present")

# 6. Status dot component
if '.status-dot' not in css:
    hard.append(".status-dot component missing")
else:
    states = re.findall(r'\.status-dot\.(\w+)', css)
    info.append(f"status-dot: {len(states)} state modifiers ({', '.join(sorted(set(states)))})")

# 7. Theme toggle JS (check core.js)
js_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'core.js')
if os.path.exists(js_path):
    js = open(js_path, encoding='utf-8').read()
    if 'themeToggle' not in js or 'portal-theme' not in js:
        hard.append("theme toggle JS missing from core.js")
    else:
        info.append("theme toggle JS present (localStorage + prefers-color-scheme)")

# --- INFORMATIONAL: token migration progress ---
token_defs = re.findall(r'--(\w+):', css[:css.find('}')])  # :root block
token_count = len(token_defs)
var_uses = len(re.findall(r'var\(--', css))
raw_hex = len(re.findall(r'#[0-9a-fA-F]{3,8}\b', css))
info.append(f"tokens: {token_count} defined, {var_uses} var() uses, {raw_hex} raw hex remaining")

# --- REPORT ---
print(f"design_check.py: ui/app.css ({os.path.getsize(css_path)} bytes)")
for i in info:
    print(f"  [info] {i}")
if hard:
    print(f"  FAIL: {len(hard)} hard violation(s):")
    for h in hard:
        print(f"    - {h}")
    sys.exit(1)
else:
    print("  PASS: 0 hard violations")
    sys.exit(0)