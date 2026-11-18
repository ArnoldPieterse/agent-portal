#!/usr/bin/env python3
"""ui_closure_check.py - live-disk verifier for UI-goal closures.

Parent: memory/ops/INDEX.md | Sibling: evidence-closure-protocol.md, stale_claim_check.py
Small file - read whole. Purpose: operationalize closure-protocol checklist item #1
("Artifact exists on disk") for DESIGNER/UI goals, which keep getting re-litigated by
hand (see designer goal #4 emptyState churn: 3+ agents re-grepped live ui/*.js over days).

A UI-goal "closed" claim is only trustworthy if the feature's code is present in the LIVE
files index.html actually loads. This tool measures that on disk and returns a hard PASS/FAIL.

Usage:
  python memory/ops/ui_closure_check.py <feature_regex> --js ui/core.js,ui/uploads.js [--css ui/app.css --css-class .empty-state]

Checks performed (all must hold for PASS):
  1. Each --js file EXISTS and contains >=1 match of <feature_regex>.
  2. Each --js file is LISTED in index.html's static <script src=...> set (a feature defined in a
     file that is never loaded cannot render -> FAIL with reason).
  3. If --css/--css-class given: the css file EXISTS and contains the class.
Exit: 0 = PASS, 1 = FAIL, 2 = usage error.
"""
import argparse, os, re, sys

def index_script_set(root):
    html = os.path.join(root, 'index.html')
    if not os.path.exists(html):
        return None
    t = open(html, encoding='utf-8', errors='ignore').read()
    srcs = re.findall(r'<script[^>]*src=[\'\"]([^\'\"]+)', t)
    norm = set()
    for s in srcs:
        # keep the ui/... tail so 'ui/core.js' matches regardless of leading slash
        norm.add(s.lstrip('/').replace('\\', '/'))
    return norm

def main():
    ap = argparse.ArgumentParser(description='live-disk verifier for UI-goal closures')
    ap.add_argument('feature', help='regex that must appear in each required JS file (e.g. emptyState)')
    ap.add_argument('--js', default='', help='comma-separated JS files the feature MUST be present in')
    ap.add_argument('--css', default='', help='CSS file to check (optional)')
    ap.add_argument('--css-class', default='', help='class/selector that must appear in --css (optional)')
    ap.add_argument('--root', default='.', help='project root (default cwd)')
    a = ap.parse_args()

    js_files = [x.strip() for x in a.js.split(',') if x.strip()]
    if not js_files:
        print('usage: need at least one --js file'); return 2
    rx = re.compile(a.feature)
    css_rx = re.compile(a.css_class) if a.css and a.css_class else None

    scripts = index_script_set(a.root)
    fails, lines = [], []
    for f in js_files:
        fp = os.path.join(a.root, f.replace('/', os.sep))
        if not os.path.exists(fp):
            fails.append(f'{f}: FILE MISSING'); lines.append(f'  [MISSING] {f}'); continue
        t = open(fp, encoding='utf-8', errors='ignore').read()
        n = len(rx.findall(t))
        loaded = (scripts is None) or (f in scripts)
        if n == 0:
            fails.append(f'{f}: feature /{a.feature}/ NOT FOUND (0 hits)')
            lines.append(f'  [NO-HIT ] {f} ({n})')
        else:
            lines.append(f'  [OK     ] {f} ({n} hit(s))')
        if not loaded and scripts is not None:
            fails.append(f'{f}: NOT in index.html <script> list -> never loads')
            lines.append(f'  [UNLOADED] {f} (absent from index.html)')
    if css_rx and a.css:
        cf = os.path.join(a.root, a.css.replace('/', os.sep))
        if not os.path.exists(cf):
            fails.append(f'{a.css}: CSS FILE MISSING'); lines.append(f'  [MISSING] {a.css}')
        else:
            ct = open(cf, encoding='utf-8', errors='ignore').read()
            cn = len(css_rx.findall(ct))
            if cn == 0:
                fails.append(f'{a.css}: /{a.css_class}/ NOT FOUND (0 hits)')
                lines.append(f'  [NO-HIT ] {a.css} ({cn})')
            else:
                lines.append(f'  [OK     ] {a.css} ({cn} hit(s))')

    verdict = 'PASS' if not fails else 'FAIL'
    print(f'feature /{a.feature}/ -> {verdict}')
    print('\n'.join(lines))
    if fails:
        print('reasons:'); [print('  -', x) for x in fails]
    return 0 if not fails else 1

if __name__ == '__main__':
    sys.exit(main())
