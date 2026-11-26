#!/usr/bin/env python3
"""Pre-pin token-enforcement gate (pixel goal #8).

Flags hardcoded hex COLOR values in the convergence + fleet JS surfaces
(ui/cockpit-*.js, ui/fleet_*.js) that should instead reference ui/tokens.css
design tokens. Excludes HTML numeric entities (&#NNNN;) and non-color '#'.

Usage:
  python memory/pixel/prepin_token_gate.py            # scan tree; exit 0 clean / 1 violations
  python memory/pixel/prepin_token_gate.py --selftest # prove it rejects an injected violation

Wired as a pre-pin check: run before advancing any index.html pin for these surfaces.
"""
import re, sys, glob, os

# Color-hex NOT immediately preceded by '&' (which would make it an HTML entity &#NNNN;).
HEXCOLOR = re.compile(r"(?<!&)#([0-9a-fA-F]{3,8})\b")

def scan_files(paths):
    """Return list of (file, line, hex, ctx) violations."""
    out = []
    for p in paths:
        try:
            lines = pathlib_open(p).splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, l in enumerate(lines, 1):
            for m in HEXCOLOR.finditer(l):
                ctx = l[max(0, m.start()-8):m.end()+2].strip()
                out.append((p, i, m.group(0), ctx))
    return out

def pathlib_open(p):
    with open(p, "r", encoding="utf-8") as fh:
        return fh.read()

def target_files():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
    ui = os.path.join(base, "ui")
    files = glob.glob(os.path.join(ui, "cockpit-*.js")) + glob.glob(os.path.join(ui, "fleet_*.js"))
    return sorted(set(files))

def selftest():
    bad  = 'el.style.color = "#ff0000";'      # real color hex -> MUST be flagged
    ent  = '<div>&#9888; warn</div>'           # HTML entity   -> must NOT be flagged
    url  = '<a href="/x#/api/goals/onepager">' # fragment       -> must NOT be flagged (no pure-hex run)
    vb = [m.group(0) for m in HEXCOLOR.finditer(bad)]
    ve = [m.group(0) for m in HEXCOLOR.finditer(ent)]
    vu = [m.group(0) for m in HEXCOLOR.finditer(url)]
    ok = (len(vb) >= 1) and (len(ve) == 0) and (len(vu) == 0)
    print("selftest: bad->%s ent->%s url->%s" % (vb, ve, vu))
    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1

def main():
    if "--selftest" in sys.argv:
        return selftest()
    files = target_files()
    viols = scan_files(files)
    if not files:
        print("GATE ERROR: no target files found under ui/")
        return 2
    if viols:
        for f, i, h, ctx in viols:
            print("VIOLATION %s:%d  %s   | %s" % (f, i, h, ctx))
        print("GATE FAIL: %d hardcoded hex color(s) outside tokens.css across %d file(s)" % (len(viols), len(files)))
        return 1
    print("PASS: 0 hardcoded hex colors in %d cockpit/fleet JS file(s) (tokens enforced)" % len(files))
    return 0

if __name__ == "__main__":
    sys.exit(main())
