#!/usr/bin/env python3
"""density_audit.py — recompute goal #2 vertical-whitespace model from live ui/app.css.
Usage: python memory/designer/density_audit.py
Deterministic (no browser). Reads :root density tokens + the 5 panel rules and
prints the before/after height table used in information-density-pass-2026-11-18.md."""
import re, sys
css = open("ui/app.css", encoding="utf-8").read()
def tok(name):
    m = re.search(r"--%s:\s*([\d.]+)" % name, css)
    return float(m.group(1)) if m else None
lh_base = tok("lh-base"); lh_mono = tok("lh-mono")
sp6 = tok("sp-6"); sp4 = tok("sp-4"); sp8 = tok("sp-8")
# after values (px)
C_panel = 2*sp6                 # --vh-panel top+bottom
R_row   = 2*sp4                 # --vh-row top+bottom
L_base  = 12*lh_base            # fs-12 body line box
L_mono  = 12*lh_mono            # fs-12 mono line box
files_R = 6                     # #filesList li padding:3px x2
ops_C   = C_panel + 6 + 6       # #opsBody vpad + .opsbox margin-top(sp-6)+padding(3+3)
# before (original) values hardcoded for the delta
PANELS=[("Fleet (8 agent rows)",16,16,12*1.45, C_panel,R_row,L_base,8),
        ("Ops log (14 mono lines)",16+16,0,12*1.6, ops_C,0,L_mono,14),
        ("Activity (16 lines)",16,0,12*1.7, C_panel,0,L_mono,16),
        ("Files (10 items)",0,8,12*1.45, 0,files_R,L_base,10),
        ("Goals (8 tiles)",16,16,20, C_panel,R_row,20,8)]
tb=ta=0
print("%-24s %8s %8s %7s"%("Panel","Before","After","d%"))
for name,Cb,Rb,Lb,Ca,Ra,La,N in PANELS:
    b=Cb+N*(Rb+Lb); a=Ca+N*(Ra+La); tb+=b; ta+=a
    print("%-24s %8.1f %8.1f %6.1f%%"%(name,b,a,(b-a)/b*100))
print("-"*52)
print("%-24s %8.1f %8.1f %6.1f%%"%("AGGREGATE",tb,ta,(tb-ta)/tb*100))
