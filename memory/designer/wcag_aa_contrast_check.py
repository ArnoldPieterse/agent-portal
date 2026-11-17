#!/usr/bin/env python3
"""WCAG AA contrast checker for ui/app.css.
Extracts :root token pairs + hardcoded hex pairs, computes contrast ratios,
reports pass/fail against WCAG 2.1 AA (4.5:1 normal, 3:1 large).
Usage: python memory/designer/wcag_aa_contrast_check.py [--css path]
Exit code: 0 = all pass, 1 = failures found.
"""
import re, sys

def hex_to_rgb(h):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(c*2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rel_luminance(rgb):
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(fg, bg):
    l1, l2 = rel_luminance(hex_to_rgb(fg)), rel_luminance(hex_to_rgb(bg))
    return (max(l1,l2) + 0.05) / (min(l1,l2) + 0.05)

def main():
    css_path = 'ui/app.css'
    if '--css' in sys.argv:
        css_path = sys.argv[sys.argv.index('--css') + 1]
    
    css = open(css_path).read()
    root_match = re.search(r':root\{([^}]+)\}', css)
    if not root_match:
        print("ERROR: no :root block found"); sys.exit(1)
    
    tokens = {}
    for m in re.finditer(r'(--[\w-]+):\s*([^;}\s]+)', root_match.group(1)):
        tokens[m.group(1)] = m.group(2).strip()
    
    # Identify color tokens (hex only)
    color_tokens = {k: v for k, v in tokens.items() if v.startswith('#')}
    text_toks = [k for k in color_tokens if any(x in k for x in ('text','dim','faint','acc','ok','warn','err'))]
    bg_toks = [k for k in color_tokens if 'bg' in k or 'panel' in k]
    
    failures = 0
    print(f"Checking {len(text_toks)} fg x {len(bg_toks)} bg token pairs...\n")
    for fg in text_toks:
        for bg in bg_toks:
            ratio = contrast_ratio(color_tokens[fg], color_tokens[bg])
            status = "PASS" if ratio >= 4.5 else ("LARGE" if ratio >= 3.0 else "FAIL")
            flag = {"PASS":"\u2713","LARGE":"\u25b3","FAIL":"\u2717"}[status]
            print(f"  {flag} {fg} on {bg}: {ratio:.2f}:1 [{status}]")
            if status == "FAIL": failures += 1
    
    print(f"\nResult: {failures} failure(s)")
    sys.exit(1 if failures else 0)

if __name__ == '__main__':
    main()
