#!/usr/bin/env python3
"""Asset budget check for portal UI files.
Closes stale claim from designer-goal-proposals-2026-11-17.md.

Per-file budgets (minified, bytes):
  ui/app.css     <= 40 KB
  ui/core.js     <= 30 KB
  ui/uploads.js  <= 10 KB
  index.html     <= 10 KB  (raw - HTML is not minified in practice)
Total budget:    <= 80 KB minified (CSS+JS) + 10 KB HTML = 90 KB effective

Usage: python memory/designer/asset_budget_check.py [--json]
Exit code: 0 = all pass, 1 = one or more over budget
"""
import os, re, sys, json

BUDGETS = {
    'ui/app.css':    {'max_bytes': 40 * 1024, 'minify': 'css'},
    'ui/core.js':    {'max_bytes': 30 * 1024, 'minify': 'js'},
    'ui/uploads.js': {'max_bytes': 10 * 1024, 'minify': 'js'},
    'index.html':    {'max_bytes': 10 * 1024, 'minify': None},
}
TOTAL_CSS_JS_BUDGET = 80 * 1024


def minify_css(content):
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    content = re.sub(r'\s+', ' ', content).strip()
    return content


def minify_js(content):
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    content = re.sub(r'//[^\n]*', '', content)
    content = re.sub(r'\s+', ' ', content).strip()
    return content


def check():
    results = []
    total_css_js_min = 0
    all_pass = True

    for path, cfg in BUDGETS.items():
        if not os.path.exists(path):
            results.append({'file': path, 'status': 'MISSING', 'raw': 0, 'minified': 0, 'budget': cfg['max_bytes']})
            all_pass = False
            continue
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        raw = len(content.encode('utf-8'))
        if cfg['minify'] == 'css':
            mn = len(minify_css(content).encode('utf-8'))
        elif cfg['minify'] == 'js':
            mn = len(minify_js(content).encode('utf-8'))
        else:
            mn = raw
        ok = mn <= cfg['max_bytes']
        if not ok:
            all_pass = False
        if path.endswith(('.css', '.js')):
            total_css_js_min += mn
        results.append({
            'file': path, 'status': 'PASS' if ok else 'OVER',
            'raw': raw, 'minified': mn, 'budget': cfg['max_budget'] if 'max_budget' in cfg else cfg['max_bytes'],
        })

    # Total CSS+JS check
    total_ok = total_css_js_min <= TOTAL_CSS_JS_BUDGET
    if not total_ok:
        all_pass = False

    return results, total_css_js_min, all_pass


def main():
    as_json = '--json' in sys.argv
    results, total, all_pass = check()

    if as_json:
        print(json.dumps({'results': results, 'total_css_js_minified': total,
                          'total_budget': TOTAL_CSS_JS_BUDGET, 'all_pass': all_pass}, indent=2))
    else:
        print(f"{'File':<16} {'Raw':>8} {'Minified':>10} {'Budget':>8} {'Status'}")
        print("-" * 54)
        for r in results:
            print(f"{r['file']:<16} {r['raw']/1024:>7.1f}K {r['minified']/1024:>9.1f}K "
                  f"{r['budget']/1024:>7.0f}K  {r['status']}")
        print("-" * 54)
        total_status = 'PASS' if total <= TOTAL_CSS_JS_BUDGET else 'OVER'
        print(f"{'CSS+JS total':<16} {'':>8} {total/1024:>9.1f}K {TOTAL_CSS_JS_BUDGET/1024:>7.0f}K  {total_status}")
        print(f"\nOverall: {'PASS' if all_pass else 'FAIL'}")

    sys.exit(0 if all_pass else 1)


if __name__ == '__main__':
    main()