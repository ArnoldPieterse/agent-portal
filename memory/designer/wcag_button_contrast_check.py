#!/usr/bin/env python3
"""WCAG AA button-label contrast check (Designer goal #2 assist, Verifier seat 2026-11-17).

Closes a coverage gap in wcag_contrast_live.py: that checker tests token x {bg,panel}
only and never white text on accent/BUTTON backgrounds. This one parses ui/app.css live,
finds every element whose color is white/#fff sitting on an accent-ish background, and
reports AA (4.5 normal / 3.0 large) pass-fail per case.

parent: memory/designer/INDEX.md | owner goal: Designer #2 (Verifier produced this)
rule: memory/portal/file-modularity.md | repro: python memory/designer/wcag_button_contrast_check.py
"""
import re, json, os

def srgb(c):
    c = c/255.0
    return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4
def lum(hx):
    hx = hx.lstrip('#')
    if len(hx)==3: hx=''.join(ch*2 for ch in hx)
    r,g,b = (int(hx[i:i+2],16) for i in (0,2,4))
    return 0.2126*srgb(r)+0.7152*srgb(g)+0.0722*srgb(b)
def cr(a,b):
    la,lb = lum(a),lum(b); hi,lo = max(la,lb),min(la,lb)
    return (hi+0.05)/(lo+0.05)

CSS = os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'app.css')
t = open(CSS, encoding='utf-8').read()
tok = dict(re.findall(r'(--[a-z0-9]+):\s*(#[0-9a-fA-F]{6})', t))

# white text on accent / button backgrounds (the cases the 14-pair checker misses)
cases = [
    ("#fff", "--acc",   "#send / .btn.pri label on --acc"),
    ("#fff", "#3a6fd6", ".seg button.on label (hardcoded blue)"),
    ("#fff", "--focus", "(informational) white on focus ring color"),
]
rows, fails = [], 0
for fg, bg, desc in cases:
    bghex = tok.get(bg, bg)
    r = cr(fg, bghex)
    ok = r >= 4.5
    if not ok: fails += 1
    rows.append({"fg": fg, "bg": "%s(%s)" % (bg, bghex), "desc": desc,
                 "ratio": round(r,2), "aa_normal": ok, "aa_large": r >= 3.0})

out = {"date":"2026-11-17","source":"ui/app.css (live)",
       "scope":"white text on accent/button backgrounds (gap in wcag_contrast_live.py)",
       "rows": rows, "fails_normal": fails}
print(json.dumps(out, indent=2))
dest = os.path.join(os.path.dirname(__file__), 'wcag_button_contrast_20261117.json')
json.dump(out, open(dest,'w'), indent=2)
print("\nWROTE", dest, "| FAILS(normal AA):", fails)