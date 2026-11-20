#!/usr/bin/env python3
"""memory/designer/contrast_audit.py - WCAG 2.1 AA contrast audit over design tokens (Designer Goal #7).

Parses ui/tokens.css (:root = dark family, [data-theme=light] = light override), computes
relative-luminance contrast for each *primary text* token against the main surface backgrounds
it actually renders on, and reports any pair below 4.5:1 (AA normal text). Exit code 0 = all pass,
1 = failures found.

Usage: python memory/designer/contrast_audit.py [--min 4.5]
Note: text-on-transient-selection-highlight (--sel-bg) is a component-level selected-state color
pattern, not covered here; see goal7 evidence leaf for the documented follow-up.
"""
import re, sys, pathlib

def parse_body(body):
    d = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", body):
        d.setdefault(m.group(1), m.group(2).strip())
    return d

def load_tokens(css_path):
    css = pathlib.Path(css_path).read_text(encoding="utf-8", errors="replace")
    # Dark family = :root blocks NOT inside a light-scheme @media query. The media-query
    # wrapper text sits BEFORE the matched braces, so detect it by scanning the preceding
    # context (a bare substring check on the body would miss it).
    dark = {}
    for m in re.finditer(r":root\s*\{([^}]*)\}", css, re.S):
        prefix = css[max(0, m.start()-80):m.start()]
        if "prefers-color-scheme" in prefix:
            continue  # light-scheme fallback block - not part of the dark family
        dark.update(parse_body(m.group(1)))
    m = re.search(r"\[data-theme=light\]\s*\{([^}]*)\}", css)
    light = dict(dark); light.update(parse_body(m.group(1)) if m else {})
    return dark, light

def h2r(h):
    h = h.lstrip("#")
    if len(h) == 3: h = "".join(c*2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0,2,4))

def lum(r):
    f = lambda c: (c/255/12.92 if c/255 <= 0.03928 else ((c/255+.055)/1.055)**2.4)
    R,G,B = [f(x) for x in r]
    return .2126*R + .7152*G + .0722*B

def contrast(a, b):
    l1, l2 = lum(h2r(a)), lum(h2r(b))
    if l1 < l2: l1, l2 = l2, l1
    return (l1+.05)/(l2+.05)

def is_color(v):
    return isinstance(v, str) and v.startswith("#") and len(v) in (4,7)

TEXTS = ["--text","--dim","--faint","--muted","--ok","--warn","--err",
         "--link","--dm-text","--int-text","--warn-text"]
DARK_SURF = {"bg":"#0e1116","panel":"#151a22","panel2":"#1b2230","queue-bg":"#0d1117","peek-bg":"#141a26"}
LIGHT_SURF = {"bg":"#f4f6fa","panel":"#ffffff","panel2":"#eef1f6","queue-bg":"#f8fafc","int-bg":"#fffbeb"}

def audit(name, tok, surf, minr):
    fails = []
    for t in TEXTS:
        if not is_color(tok.get(t, "")): continue
        for b, bv in surf.items():
            c = contrast(tok[t], bv)
            if c < minr: fails.append((c, t, b, tok[t]))
    print(f"== {name} (min {minr}:1) ==")
    for c, t, b, fg in sorted(fails):
        print(f"  FAIL {c:.2f}:1  {t} on --{b}  ({fg})")
    if not fails: print("  ALL PASS")
    return fails

def main():
    minr = 4.5
    args = sys.argv[1:]
    if "--min" in args:
        i = args.index("--min"); minr = float(args[i+1])
    root = pathlib.Path(__file__).resolve().parents[2]
    dark, light = load_tokens(root / "ui/tokens.css")
    f1 = audit("DARK", dark, DARK_SURF, minr)
    f2 = audit("LIGHT", light, LIGHT_SURF, minr)
    total = len(f1) + len(f2)
    print(f"\nRESULT: {total} failing pair(s)")
    sys.exit(1 if total else 0)

if __name__ == "__main__":
    main()
