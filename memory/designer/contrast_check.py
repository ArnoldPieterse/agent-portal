"""WCAG AA Contrast Verification for Agent Portal UI tokens.
Reads token values from ui/app.css, computes contrast ratios for all
foreground/background pairs in both themes, and reports pass/fail.

Usage: python memory/designer/contrast_check.py
Exit code 0 = all pass, 1 = failures found."""

import re, sys, os

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rel_luminance(rgb):
    r, g, b = [c / 255.0 for c in rgb]
    def chan(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = chan(r), chan(g), chan(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(fg_hex, bg_hex):
    fl = rel_luminance(hex_to_rgb(fg_hex))
    bl = rel_luminance(hex_to_rgb(bg_hex))
    return (max(fl, bl) + 0.05) / (min(fl, bl) + 0.05)

def extract_tokens(css_text):
    """Extract --var:#hex pairs from :root and [data-theme="light"] blocks."""
    dark = {}
    light = {}
    m = re.search(r':root\{([^}]+)\}', css_text)
    if m:
        for var, val in re.findall(r'(--\w+):(#[0-9a-fA-F]{6})', m.group(1)):
            dark[var] = val
    m = re.search(r'\[data-theme="light"\]\{([^}]+)\}', css_text)
    if m:
        for var, val in re.findall(r'(--\w+):(#[0-9a-fA-F]{6})', m.group(1)):
            light[var] = val
    return dark, light

PAIRS = [
    ('--text',   '--bg',     'body text on bg',          4.5),
    ('--text',   '--panel',  'header/aside text',        4.5),
    ('--text',   '--panel2', 'card/message text',        4.5),
    ('--dim',    '--bg',     'secondary text on bg',     4.5),
    ('--dim',    '--panel',  'secondary text in panel',  4.5),
    ('--dim',    '--panel2', 'secondary text in card',   4.5),
    ('--faint',  '--bg',     'faint label on bg',        4.5),
    ('--acc',    '--bg',     'accent on bg (link)',      3.0),
    ('--ok',     '--bg',     'status ok dot',            3.0),
    ('--warn',   '--bg',     'status warn dot',          3.0),
    ('--err',    '--bg',     'status err dot',           3.0),
    ('--focus',  '--bg',     'focus ring on bg',         3.0),
]

def main():
    css_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'app.css')
    if not os.path.exists(css_path):
        css_path = 'ui/app.css'
    with open(css_path, 'r', encoding='utf-8') as f:
        css_text = f.read()

    dark, light = extract_tokens(css_text)
    all_pass = True

    for name, tokens in [('DARK (:root)', dark), ('LIGHT [data-theme="light"]', light)]:
        print(f"\n{'='*60}")
        print(f"  {name}")
        print(f"{'='*60}")
        print(f"  {'Pair':<28} {'Ratio':>7} {'Min':>5}  Status")
        print(f"  {'-'*28} {'-'*7} {'-'*5}  {'-'*6}")
        for fg, bg, label, min_r in PAIRS:
            if fg not in tokens or bg not in tokens:
                print(f"  {fg+' on '+bg:<28} {'MISSING':>7}  SKIP")
                continue
            ratio = contrast_ratio(tokens[fg], tokens[bg])
            ok = ratio >= min_r
            if not ok:
                all_pass = False
            status = "PASS" if ok else "FAIL"
            print(f"  {fg+' on '+bg:<28} {ratio:>5.2f}:1 {min_r:>4.1f}  {status}")

    total = len(PAIRS) * 2
    passed = sum(1 for tokens in [dark, light]
                 for fg, bg, _, min_r in PAIRS
                 if fg in tokens and bg in tokens
                 and contrast_ratio(tokens[fg], tokens[bg]) >= min_r)

    print(f"\n{'='*60}")
    print(f"RESULT: {passed}/{total} pairs meet WCAG AA {'PASS' if all_pass else 'FAIL'}")
    print(f"{'='*60}")
    return 0 if all_pass else 1

if __name__ == '__main__':
    sys.exit(main())
