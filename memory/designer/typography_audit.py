#!/usr/bin/env python3
"""Goal #8 typography audit - checks ui/app.css for line-height, letter-spacing,
font-weight steps, and hardcoded color leaks. Run: python memory/designer/typography_audit.py"""
import re, sys, os

css_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'app.css')
css = open(css_path, encoding='utf-8').read()

failures = []

# 1. line-height values
print('=== LINE-HEIGHT ===')
lh_matches = re.findall(r'line-height\s*:\s*([\d.]+)', css)
if not lh_matches:
    print('  No explicit line-height (body inherits 1.45) - OK')
else:
    for v in lh_matches:
        fv = float(v)
        ok = 0.8 <= fv <= 2.0
        status = 'OK' if ok else 'OUT-OF-RANGE'
        print(f'  line-height: {v} [{status}]')
        if not ok:
            failures.append(f'line-height {v} out of range')

# 2. letter-spacing on uppercase labels
print('\n=== UPPERCASE LETTER-SPACING ===')
upper_rules = re.findall(r'([^{}]+)\{[^}]*text-transform\s*:\s*uppercase[^}]*\}', css)
if not upper_rules:
    print('  No text-transform:uppercase rules found')
else:
    for r in upper_rules:
        selector = r.strip()[:80]
        block = re.search(rf'{re.escape(selector.strip())}\{{([^}}]*)\}}', css)
        has_ls = 'letter-spacing' in (block.group(1) if block else '')
        ls_val = re.search(r'letter-spacing\s*:\s*([^;]+)', block.group(1)) if block and has_ls else None
        print(f'  {selector} -> letter-spacing: {ls_val.group(1).strip() if ls_val else "MISSING"}')
        if not has_ls:
            failures.append(f'{selector} missing letter-spacing')

# 3. font-weight steps
print('\n=== FONT-WEIGHT STEPS ===')
fw_values = set(re.findall(r'font-weight\s*:\s*(\d+|normal|bold)', css))
numeric_fw = sorted(set(int(v) for v in fw_values if v.isdigit()))
normal_map = {'normal': 400, 'bold': 700}
for v in fw_values:
    if v in normal_map and normal_map[v] not in numeric_fw:
        numeric_fw.append(normal_map[v])
numeric_fw.sort()
print(f'  Distinct weights: {numeric_fw}')
if len(numeric_fw) >= 3:
    print('  PASS: >=3 meaningful font-weight steps')
else:
    failures.append(f'Only {len(numeric_fw)} font-weight steps (need >=3)')

# 4. Hardcoded hex outside token blocks
print('\n=== HARDCODED HEX OUTSIDE TOKENS ===')
stripped = re.sub(r':root\{[^}]*\}', '', css)
stripped = re.sub(r'\[data-theme[^\]]*\]\{[^}]*\}', '', stripped)
hexes = re.findall(r'#[0-9a-fA-F]{3,8}\b', stripped)
if hexes:
    print(f'  Found {len(hexes)} hardcoded hex values:')
    for h in sorted(set(hexes)):
        idx = stripped.find(h)
        ctx = stripped[max(0,idx-50):idx+len(h)+20].replace('\n',' ')
        print(f'    {h} -> ...{ctx.strip()[:80]}...')
    failures.append(f'{len(hexes)} hardcoded hex values outside :root/[data-theme]')
else:
    print('  None found - PASS')

# 5. Check for missing line-height on body (should be 1.2-1.6)
print('\n=== BODY LINE-HEIGHT ===')
body_lh = re.search(r'body\{[^}]*line-height\s*:\s*([\d.]+)', css)
if body_lh:
    v = float(body_lh.group(1))
    ok = 1.2 <= v <= 1.6
    print(f'  body line-height: {body_lh.group(1)} [{"OK" if ok else "CHECK"}]')
else:
    print('  No explicit body line-height found')
    failures.append('body has no explicit line-height')

print('\n' + '='*50)
if failures:
    print(f'RESULT: FAIL ({len(failures)} issue(s))')
    for f in failures:
        print(f'  - {f}')
    sys.exit(1)
else:
    print('RESULT: PASS - all typography checks satisfied')
