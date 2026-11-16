#!/usr/bin/env python3
"""Rebuild cycle-2 design token layer + dark-mode toggle into live index.html.

Source of truth: memory/portal/design-tokens-live.md (complete value table).
The full working copy was lost to an SMB-mirror clobber; this script re-applies
deterministically and idempotently. Run:  python rebuild_tokens_darkmode_2026-11-16.py
"""
import re, hashlib, sys, datetime

PATH = 'index.html'
t = open(PATH, encoding='utf-8').read()
orig_sha = hashlib.sha1(t.encode()).hexdigest()[:12]
report = []

# --- 1. Extend :root with radius / shadow / motion families -----------------
ROOT_ADD = ('--r-sm:8px;--r-md:12px;'            # radius (was hardcoded x27/x2)
            '--shadow:0 8px 24px rgba(0,0,0,.5);--shadow-sm:0 2px 8px rgba(0,0,0,.35);'
            '--dur-fast:.12s;--dur-base:.15s;--dur-slow:.2s;')  # motion (all <=200ms)

root_m = re.search(r'(:root\{)([^}]*)(\})', t, re.S)
if root_m and '--r-sm' not in root_m.group(2):
    t = t[:root_m.start()] + root_m.group(1) + root_m.group(2) + ROOT_ADD + root_m.group(3) + t[root_m.end():]
    report.append('ROOT: appended radius/shadow/motion tokens')
elif '--r-sm' in t:
    report.append('ROOT: already has --r-sm (skip)')
else:
    report.append('ROOT: FAILED to locate :root block'); sys.exit(1)

# --- 2. Wire hardcoded radius literals -> vars (leave 50% circles) ----------
n8 = len(re.findall(r'border-radius:\s*8px\b', t))
n12 = len(re.findall(r'border-radius:\s*12px\b', t))
t = re.sub(r'border-radius:\s*8px\b',  'border-radius:var(--r-sm)', t)
t = re.sub(r'border-radius:\s*12px\b', 'border-radius:var(--r-md)', t)
report.append(f'RADIUS: {n8}x8px->var(--r-sm), {n12}x12px->var(--r-md); 50% circles left={len(re.findall(chr(98)+"order-radius:\s*50%", t))}')

# --- 3. Wire #peek box-shadow literal -> var(--shadow) ----------------------
nsh = len(re.findall(r'box-shadow:\s*0 8px 24px rgba\(0,0,0,\.5\)', t))
t = re.sub(r'box-shadow:\s*0 8px 24px rgba\(0,0,0,\.5\)', 'box-shadow:var(--shadow)', t)
report.append(f'SHADOW: {nsh}x literal->var(--shadow)')

# --- 4. Light-theme override block (full light palette + soft shadows) ------
LIGHT = (
 '[data-theme="light"]{'
 '--bg:#f4f6fa;--panel:#ffffff;--panel2:#eaeef4;--line:#d3dae4;'
 '--text:#1a212b;--dim:#586475;--acc:#2563d9;--ok:#117a48;--warn:#9c5400;'
 '--err:#bd3030;--focus:#2563d9;--faint:#7c8798;'
 '--shadow:0 8px 24px rgba(20,30,50,.12);--shadow-sm:0 2px 8px rgba(20,30,50,.08);}'
)
if 'data-theme="light"' not in t:
    root_m = re.search(r':root\{[^}]*\}', t, re.S)
    ins = root_m.end()
    t = t[:ins] + '\n' + LIGHT + t[ins:]
    report.append('LIGHT: inserted [data-theme=light] override after :root')
else:
    report.append('LIGHT: already present (skip)')

# --- 5. #themeToggle style + reduced-motion guard ---------------------------
EXTRA_CSS = (
 '#themeToggle{cursor:pointer;background:var(--panel2);color:var(--text);'
 'border:1px solid var(--line);border-radius:var(--r-sm);padding:0 var(--sp-8);'
 'font-size:var(--fs-13);transition:border-color var(--dur-fast),background-color var(--dur-fast)}'
 '#themeToggle:hover{border-color:var(--acc)}'
 '@media(prefers-reduced-motion:reduce){*{transition-duration:.001ms!important;animation-duration:.001ms!important}}'
)
if 'prefers-reduced-motion' not in t:
    ins = t.find('</style>')
    if ins == -1: ins = t.find('</head>')
    t = t[:ins] + EXTRA_CSS + t[ins:]
    report.append('CSS: added #themeToggle style + reduced-motion guard')
else:
    report.append('CSS: reduced-motion already present (skip)')

# --- 6. themeToggle button in header toolbar --------------------------------
if 'id="themeToggle"' not in t:
    anchor = 'id="fleetBtn"'
    ai = t.find(anchor)
    if ai != -1:
        # step back to the start of that <button ...> tag
        bs = t.rfind('<', 0, ai)
        btn = '<button id="themeToggle" title="Toggle theme">\U0001F319</button>'
        t = t[:bs] + btn + ' ' + t[bs:]
        report.append('TOGGLE: inserted #themeToggle before fleetBtn')
    else:
        report.append('TOGGLE: fleetBtn anchor not found (skip)')
else:
    report.append('TOGGLE: already present (skip)')

# --- 7. FOUC-free theme init script in <head> -------------------------------
HEAD_SCRIPT = (
 '<script>(function(){var k="ap-theme";'
 'function sys(){return window.matchMedia&&matchMedia("(prefers-color-scheme: light)").matches?"light":"dark"} '
 'function apply(x){document.documentElement.setAttribute("data-theme",x);'
 'var b=document.getElementById("themeToggle");if(b)b.textContent=x==="light"?"\U0001F319":"\u2600\uFE0F"} '
 'var s=null;try{s=localStorage.getItem(k)}catch(e){} apply(s||sys()); '
 'document.addEventListener("DOMContentLoaded",function(){'
 'var b=document.getElementById("themeToggle");if(!b)return; '
 'b.addEventListener("click",function(){var c=document.documentElement.getAttribute("data-theme")||"dark";'
 'var n=c==="light"?"dark":"light";apply(n);try{localStorage.setItem(k,n)}catch(e){}}); '
 'if(matchMedia){matchMedia("(prefers-color-scheme: light)").addEventListener("change",function(e){'
 'var sv=null;try{sv=localStorage.getItem(k)}catch(x){}if(!sv)apply(e.matches?"light":"dark")})}});})();</script>'
)
if 'ap-theme' not in t:
    ins = t.find('</head>')
    t = t[:ins] + HEAD_SCRIPT + t[ins:]
    report.append('SCRIPT: inserted FOUC-free theme init before </head>')
else:
    report.append('SCRIPT: ap-theme already present (skip)')

# --- Write back -------------------------------------------------------------
open(PATH, 'w', encoding='utf-8').write(t)
new_sha = hashlib.sha1(t.encode()).hexdigest()[:12]

print('rebuild_tokens_darkmode  %s' % datetime.datetime.now().isoformat(timespec='seconds'))
print('index.html sha12: %s -> %s  (%d -> %d bytes)' % (orig_sha, new_sha, len(orig_sha and t), len(t)))
for line in report: print(' -', line)

# --- Verification grep ------------------------------------------------------
v = open(PATH, encoding='utf-8').read()
print('\nVERIFY:')
print('  --r-sm present:', '--r-sm' in v, '| count var(--r-sm):', v.count('var(--r-sm)'))
print('  --dur-fast present:', '--dur-fast' in v)
print('  remaining border-radius:8px literals:', len(re.findall(r'border-radius:\s*8px\b', v)))
print('  remaining border-radius:12px literals:', len(re.findall(r'border-radius:\s*12px\b', v)))
print('  box-shadow literal remaining:', '0 8px 24px rgba(0,0,0,.5)' in v and not v.count('box-shadow:var(--shadow)'))
print('  data-theme=light override:', 'data-theme="light"' in v)
print('  themeToggle button:', 'id="themeToggle"' in v)
print('  ap-theme script:', 'ap-theme' in v)
print('  prefers-reduced-motion guard:', 'prefers-reduced-motion' in v)

# --- Re-pin canonical snapshot so the mirror cannot silently drop it --------
pin = 'memory/designer/index_html_CANONICAL_%s_2026-11-16e.html' % new_sha
open(pin, 'w', encoding='utf-8').write(v)
print('\nPINNED ->', pin)
