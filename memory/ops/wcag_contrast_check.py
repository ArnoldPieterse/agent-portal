#!/usr/bin/env python3
"""WCAG AA Contrast Ratio Checker for portal design tokens.

Parses ui/tokens.css, extracts color tokens for each theme, computes WCAG 2.x
contrast ratios for all meaningful text/background pairs, and reports pass/fail.

Usage:
    python memory/ops/wcag_contrast_check.py [--theme light|dark|all] [--json]

Exit codes: 0 = all pass, 1 = one or more failures, 2 = parse error.

Cross-ref: Builder patch at memory/ops/wcag-aa-light-theme-fixes-2026-11-23.md
"""
import re, sys, os, json, math

def hex_to_rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c*2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rel_luminance(rgb):
    """WCAG 2.x relative luminance."""
    def srgb_to_linear(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (srgb_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(hex1, hex2):
    l1 = rel_luminance(hex_to_rgb(hex1))
    l2 = rel_luminance(hex_to_rgb(hex2))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def parse_tokens(css_text):
    """Extract named hex tokens from CSS blocks."""
    themes = {}
    # Dark theme: :root{...} blocks (first one is the main dark family)
    for m in re.finditer(r':root\{([^}]+)\}', css_text):
        block = m.group(1)
        tokens = dict(re.findall(r'--(\w+):\s*(#[0-9a-fA-F]{3,8})', block))
        if 'dark' not in themes:
            themes['dark'] = tokens
        else:
            themes['dark'].update(tokens)
    # Light theme: [data-theme=light]{...}
    for m in re.finditer(r'\[data-theme=light\]\{([^}]+)\}', css_text):
        block = m.group(1)
        tokens = dict(re.findall(r'--(\w+):\s*(#[0-9a-fA-F]{3,8})', block))
        themes.setdefault('light', {}).update(tokens)
    return themes

# Pairs to check: (foreground token, background token, requirement label)
# Text on background: 4.5:1 (AA normal text)
# Non-text (icons, status dots): 3:1 (SC 1.4.11)
TEXT_PAIRS = [
    ('text', 'bg', 4.5),
    ('dim', 'bg', 4.5),
    ('faint', 'bg', 4.5),
    ('acc', 'bg', 4.5),
    ('ok', 'bg', 4.5),
    ('warn', 'bg', 4.5),
    ('err', 'bg', 4.5),
    ('link', 'bg', 4.5),
    ('text', 'panel', 4.5),
    ('dim', 'panel', 4.5),
    ('faint', 'panel', 4.5),
    ('acc', 'panel', 4.5),
    ('ok', 'panel', 4.5),
    ('warn', 'panel', 4.5),
    ('err', 'panel', 4.5),
    ('link', 'panel', 4.5),
]
NON_TEXT_PAIRS = [
    ('dot-idle', 'bg', 3.0),
    ('dot-busy', 'bg', 3.0),
    ('dot-err', 'bg', 3.0),
]
# Decorative borders are informational-only (not a hard fail)
INFORMATIONAL_PAIRS = [
    ('line', 'bg', 3.0),
]

def check_theme(tokens, theme_name):
    results = []
    for fg, bg, min_ratio in TEXT_PAIRS + NON_TEXT_PAIRS:
        fg_hex = tokens.get(fg)
        bg_hex = tokens.get(bg)
        if not fg_hex or not bg_hex:
            continue
        ratio = contrast_ratio(fg_hex, bg_hex)
        passed = ratio >= min_ratio
        results.append({
            'pair': f'--{fg} on --{bg}',
            'fg': fg_hex, 'bg': bg_hex,
            'ratio': round(ratio, 2),
            'required': min_ratio,
            'pass': passed,
            'hard': True
        })
    for fg, bg, min_ratio in INFORMATIONAL_PAIRS:
        fg_hex = tokens.get(fg)
        bg_hex = tokens.get(bg)
        if not fg_hex or not bg_hex:
            continue
        ratio = contrast_ratio(fg_hex, bg_hex)
        results.append({
            'pair': f'--{fg} on --{bg} (decorative)',
            'fg': fg_hex, 'bg': bg_hex,
            'ratio': round(ratio, 2),
            'required': min_ratio,
            'pass': ratio >= min_ratio,
            'hard': False
        })
    return results

def main():
    args = sys.argv[1:]
    theme_filter = 'all'
    as_json = '--json' in args
    for a in args:
        if a.startswith('--theme='):
            theme_filter = a.split('=', 1)[1]

    css_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'tokens.css')
    if not os.path.exists(css_path):
        print(f"ERROR: {css_path} not found", file=sys.stderr)
        return 2

    css_text = open(css_path).read()
    themes = parse_tokens(css_text)

    all_results = {}
    total_fail = 0
    for tname in ('dark', 'light'):
        if theme_filter not in ('all', tname):
            continue
        if tname not in themes:
            print(f"WARNING: no {tname} theme tokens found", file=sys.stderr)
            continue
        results = check_theme(themes[tname], tname)
        all_results[tname] = results
        fails = [r for r in results if not r['pass'] and r.get('hard', True)]
        total_fail += len(fails)

    if as_json:
        print(json.dumps(all_results, indent=2))
    else:
        for tname, results in all_results.items():
            print(f"\n=== {tname.upper()} THEME ===")
            fails = [r for r in results if not r['pass']]
            passes = [r for r in results if r['pass']]
            for r in results:
                mark = 'PASS' if r['pass'] else ('INFO' if not r.get('hard', True) else 'FAIL')
                print(f"  [{mark}] {r['pair']:35s}  {r['ratio']:5.2f}:1 (need {r['required']:.1f})")
            print(f"  Summary: {len(passes)} pass / {len(fails)} fail of {len(results)} checked")

    if total_fail > 0:
        print(f"\nRESULT: FAIL ({total_fail} pair(s) below WCAG AA threshold)", file=sys.stderr)
        return 1
    print("\nRESULT: ALL PASS (WCAG AA)", file=sys.stderr)
    return 0

if __name__ == '__main__':
    sys.exit(main())
