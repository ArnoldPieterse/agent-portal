#!/usr/bin/env python3
"""WCAG AA contrast checker for portal CSS tokens.

Usage: python memory/designer/wcag_contrast_check.py [css_path]
Checks all foreground/background token pairs against WCAG 2.1 AA thresholds.
Exit code 0 = all pass, 1 = failures found.

Pairs are defined in PAIRS below; add new pairs as themes/components grow.
"""
import re, sys

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c*2 for c in hex_str)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def relative_luminance(rgb):
    def srgb_to_linear(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (srgb_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(color1, color2):
    l1 = relative_luminance(hex_to_rgb(color1))
    l2 = relative_luminance(hex_to_rgb(color2))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

# Token pairs to check: (fg_token, bg_token, label)
PAIRS = [
    ("--text", "--bg", "Body text on page background"),
    ("--text", "--panel", "Body text on panel"),
    ("--text", "--panel2", "Body text on elevated panel"),
    ("--dim", "--bg", "Dim/secondary text on page bg"),
    ("--dim", "--panel", "Dim/secondary text on panel"),
    ("--faint", "--bg", "Faint text on page bg"),
    ("--faint", "--panel", "Faint text on panel"),
    ("--acc", "--bg", "Accent on page bg (links, highlights)"),
    ("--acc", "--panel", "Accent on panel"),
    ("--ok", "--bg", "OK/success on page bg"),
    ("--ok", "--panel", "OK/success on panel"),
    ("--warn", "--bg", "Warning on page bg"),
    ("--warn", "--panel", "Warning on panel"),
    ("--err", "--bg", "Error on page bg"),
    ("--err", "--panel", "Error on panel"),
    ("--focus", "--bg", "Focus ring color on page bg"),
]

def main():
    css_path = sys.argv[1] if len(sys.argv) > 1 else "ui/app.css"
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    tokens = dict(re.findall(r'(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8})', css))

    print("=" * 72)
    print(f"WCAG AA Contrast Check — {css_path}")
    print(f"Tokens parsed: {len(tokens)}")
    print("=" * 72)
    print(f"\n{'Pair':<45} {'Ratio':>6} {'AA-Norm':>8} {'AA-Large':>9}")
    print("-" * 72)

    failures = 0
    for fg_token, bg_token, label in PAIRS:
        fg = tokens.get(fg_token)
        bg = tokens.get(bg_token)
        if not fg or not bg:
            print(f"  SKIP {fg_token}/{bg_token} — token missing")
            continue
        ratio = contrast_ratio(fg, bg)
        aa_norm = "PASS" if ratio >= 4.5 else "FAIL"
        aa_large = "PASS" if ratio >= 3.0 else "FAIL"
        mark = "" if aa_norm == "PASS" else " ⚠️"
        if aa_norm == "FAIL":
            failures += 1
        print(f"  {label:<43} {ratio:>5.2f}:1 {aa_norm:>8} {aa_large:>9}{mark}")

    print("-" * 72)
    total = len(PAIRS)
    print(f"\nResult: {total - failures}/{total} pairs pass AA normal (4.5:1)")
    if failures:
        print(f"  → {failures} pair(s) below 4.5:1")
        sys.exit(1)
    else:
        print("  → All foreground/background pairs meet WCAG AA for normal text ✓")

if __name__ == "__main__":
    main()
