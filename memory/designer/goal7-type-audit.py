#!/usr/bin/env python3
# Goal 7 (Designer) - Typography Hierarchy Audit acceptance script.
# Acceptance: "computed styles audit (DevTools or script) shows 0 violations of the
# 5-step scale" (h1=24 h2=18 h3=15 body=14 caption=12).
#
# This is a STATIC source audit: it resolves every font-size declaration in the UI
# (CSS token refs + literal px, plus JS-injected inline styles and SVG font-size attrs)
# to its pixel value and flags anything not on the 5-step scale. Dynamic generated
# sizes are whitelisted only where they snap via nearestScale() (components.js gauge).
#
# Run:  python memory/designer/goal7-type-audit.py
# Exit 0 = PASS (0 violations), exit 1 = FAIL.
import re, glob, io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ALLOWED = {12, 14, 15, 18, 24}

def main():
    tok = io.open(os.path.join(ROOT, "ui/tokens.css"), encoding="utf-8").read()
    defs = {k: int(v) for k, v in re.findall(r"--(fs-\d+)\s*:\s*(\d+)px", tok)}

    off = []
    def check(file, line_no, val_px):
        if int(val_px) not in ALLOWED:
            off.append((file, line_no, "off-scale %s" % val_px))

    bad_defs = {k: v for k, v in defs.items() if v not in ALLOWED}
    if bad_defs:
        off.append(("ui/tokens.css", 0, "off-scale TOKEN DEFINITIONS %s" % bad_defs))

    for f in ["ui/app.css", "ui/tokens.css"]:
        p = os.path.join(ROOT, f)
        for i, line in enumerate(io.open(p, encoding="utf-8").read().splitlines(), 1):
            for m in re.finditer(r"font-size\s*:\s*([^;}]+)", line):
                v = m.group(1).strip()
                tm = re.match(r"var\(--(fs-\d+)\)", v)
                if tm:
                    if tm.group(1) not in defs:
                        off.append((f, i, "undefined token %s" % v))
                    else:
                        check(f, i, defs[tm.group(1)])
                else:
                    pm = re.match(r"([\d.]+)px", v)
                    if pm: check(f, i, pm.group(1))
                    else: off.append((f, i, "unparsed %s" % v))

    for f in glob.glob(os.path.join(ROOT, "ui", "*.js")):
        rel = os.path.relpath(f, ROOT).replace("\\", "/")
        for i, line in enumerate(io.open(f, encoding="utf-8").read().splitlines(), 1):
            for m in re.finditer(r"font-size\s*:\s*([\d.]+)px", line):
                check(rel, i, m.group(1))
            for m in re.finditer(r'font-size="(\d+)"', line):
                check(rel, i, m.group(1))
            if "Math.round(size" in line:
                off.append((rel, i, "dynamic size not snapped via nearestScale"))

    print("Defined fs tokens:", defs)
    if off:
        print("FAIL - %d violation(s):" % len(off))
        for o in off: print("  ", o)
        return 1
    print("PASS - every font-size resolves to the 5-step scale {12,14,15,18,24}; 0 violations.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
