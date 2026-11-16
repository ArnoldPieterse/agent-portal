#!/usr/bin/env python3
"""WCAG AA contrast check for both portal themes (goal #2 evidence)."""
import sys

def luminance(r, g, b):
    def s(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * s(r) + 0.7152 * s(g) + 0.0722 * s(b)

def contrast(c1, c2):
    l1 = luminance(*c1)
    l2 = luminance(*c2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

# Values extracted from ui/app.css :root and [data-theme="light"]
dark = {
    'bg': (26, 35, 50), 'panel': (30, 41, 59), 'text': (226, 232, 240),
    'dim': (156, 163, 175), 'acc': (96, 165, 250), 'ok': (74, 222, 128),
    'warn': (251, 191, 36), 'err': (248, 113, 113),
}
light = {
    'bg': (245, 246, 248), 'panel': (255, 255, 255), 'text': (26, 35, 50),
    'dim': (75, 85, 99), 'acc': (37, 99, 235), 'ok': (22, 163, 74),
    'warn': (180, 83, 9), 'err': (220, 38, 38),
}

pairs = [('text', 'bg'), ('dim', 'bg'), ('acc', 'bg'), ('ok', 'bg'),
         ('warn', 'bg'), ('err', 'bg'), ('text', 'panel'), ('dim', 'panel')]

print(f"{'Pair':<14} {'Dark':>6} {'Light':>6}  Status")
print("-" * 42)
all_pass = True
for fg, bg in pairs:
    dc = contrast(dark[fg], dark[bg])
    lc = contrast(light[fg], light[bg])
    d_ok = dc >= 4.5
    l_ok = lc >= 4.5
    if not (d_ok and l_ok):
        all_pass = False
    print(f"{fg}-{bg:<8} {dc:>5.2f}  {lc:>5.2f}  {'PASS' if d_ok else 'FAIL'}/{'PASS' if l_ok else 'FAIL'}")

print()
if all_pass:
    print("RESULT: ALL PASS (WCAG AA >=4.5:1) in both themes")
    sys.exit(0)
else:
    print("RESULT: FAILURES DETECTED")
    sys.exit(1)
