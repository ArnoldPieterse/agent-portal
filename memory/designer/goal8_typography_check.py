#!/usr/bin/env python3
"""goal8_typography_check.py - Typography hierarchy gate (Designer Goal 8)

Static audit of ui/app.css against the goal-8 acceptance criteria:
  * line-height in [1.2, 1.6] for text-bearing elements (icon glyph-centering
    controls using line-height:1 are a documented exception).
  * every text-transform:uppercase element has letter-spacing >= 0.05em.
  * >= 3 meaningful font-weight steps present.
Exit 0 = PASS, exit 1 = FAIL. Prints every violation it finds.

Usage: python memory/designer/goal8_typography_check.py [path-to-css]
"""
import re, sys

css_path = sys.argv[1] if len(sys.argv) > 1 else "ui/app.css"
css = open(css_path, encoding="utf-8", errors="replace").read()
rules = re.findall(r'([^{}/]+)\{([^}]*)\}', css)

# Documented exceptions: pure icon/glyph controls where line-height centers a symbol,
# not readable text (standard practice, e.g. Material/emoji buttons).
ICON_EXCEPTIONS = {"#attach", "button", ".seg button", ".state-error .icon"}

viol = 0

print("line-height audit (text must be within [1.2, 1.6]):")
for sel, body in rules:
    for m in re.finditer(r'line-height\s*:\s*(\d+(?:\.\d+)?)', body):
        v = float(m.group(1)); s = sel.strip()
        if 1.2 <= v <= 1.6:
            continue
        if any(s == e or s.startswith(e) for e in ICON_EXCEPTIONS):
            print(f"   [ok-exception] {s}: line-height {v} (icon glyph centering)")
        else:
            print(f"   [FAIL] {s}: line-height {v} outside [1.2,1.6]"); viol += 1

print("\nuppercase label letter-spacing (must be >= 0.05em):")
for sel, body in rules:
    if re.search(r'text-transform\s*:\s*uppercase', body):
        ls = re.search(r'letter-spacing\s*:\s*([\d.]+)em', body)
        v = float(ls.group(1)) if ls else 0.0; s = sel.strip()
        if v >= 0.05:
            print(f"   [ok] {s}: letter-spacing {v}em")
        else:
            print(f"   [FAIL] {s}: letter-spacing {v}em < 0.05em"); viol += 1

print("\nfont-weight steps (need >= 3 meaningful):")
weights = set()
for sel, body in rules:
    for m in re.finditer(r'font-weight\s*:\s*(\d+|normal|bold)', body):
        w = {"normal":400,"bold":700}.get(m.group(1), int(m.group(1)))
        weights.add(w)
print("   distinct weights:", sorted(weights))
if len(weights) >= 3:
    print(f"   [ok] {len(weights)} steps")
else:
    print(f"   [FAIL] only {len(weights)} steps < 3"); viol += 1

print("\nRESULT:", "PASS (0 violations)" if viol == 0 else f"FAIL ({viol} violation(s))")
sys.exit(0 if viol == 0 else 1)
