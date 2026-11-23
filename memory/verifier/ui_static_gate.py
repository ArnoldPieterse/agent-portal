"""
UI Static Gate - Pre-Playwright structural verification for the Fleet Cockpit.
Runs in sandbox without a browser; catches DOM/CSS/JS issues before they reach Playwright.

Checks (3 viewport widths: 768, 1024, 1400):
  1. Panel structure: all expected panel IDs exist in index.html
  2. CSS layout: no overflow:hidden clipping interactive controls at narrow widths;
     flex-shrink:0 on .seg/.toggles (regression guard for mode-button squeeze)
  3. JS syntax: all ui/*.js files parse without errors (basic bracket/quote balance)
  4. Accessibility: buttons have non-empty text or aria-label; :focus-visible styles exist

Usage:
  python memory/verifier/ui_static_gate.py --self-test   # run built-in tests
  python memory/verifier/ui_static_gate.py               # live scan of ui/ + index.html
"""
import re, json, sys, pathlib, time
from datetime import datetime, timezone

BASE = pathlib.Path(__file__).resolve().parent.parent.parent  # project root
UI_DIR = BASE / 'ui'
INDEX_HTML = BASE / 'index.html'

# Expected panel IDs (from cockpit layout - match actual index.html)
EXPECTED_PANELS = [
    'modeBar',       # Solo/Group segmented control
    'goalBar',       # goal progress bar (camelCase in HTML)
    'fleetPanel',    # fleet health
]

# CSS selectors that MUST contain specific properties (regression guards)
# Format: (selector, property, value, description)
REQUIRED_CSS_PROPS = [
    ('.seg', 'flex', 'none', '.seg must not flex-shrink (squeeze bug guard)'),
    ('.toggles', 'flex', 'none', '.toggles must not flex-shrink'),
]

# CSS rules that MUST NOT appear on interactive containers (would clip content)
FORBIDDEN_PATTERNS = [
    (r'#modeBar\s*\{[^}]*overflow\s*:\s*hidden', '#modeBar must not have overflow:hidden'),
]

VIEWPORTS = [768, 1024, 1400]


def read_file(p: pathlib.Path) -> str:
    return p.read_text(encoding='utf-8') if p.exists() else ''


def check_panels(html: str) -> list[dict]:
    """Verify expected panel IDs exist in HTML."""
    results = []
    for pid in EXPECTED_PANELS:
        found = f'id="{pid}"' in html or f"id='{pid}'" in html
        results.append({'panel': pid, 'found': found})
    return results


def check_css(css: str) -> list[dict]:
    """Check required and forbidden CSS rules."""
    results = []
    # Extract all rule blocks: selector { body }
    rule_pattern = re.compile(r'([^{}]+)\{([^{}]*)\}')
    rules = {}
    for m in rule_pattern.finditer(css):
        sel = m.group(1).strip()
        body = m.group(2).strip()
        if sel not in rules:
            rules[sel] = []
        rules[sel].append(body)

    # Required properties: check selector has the property:value
    for selector, prop, value, desc in REQUIRED_CSS_PROPS:
        found = False
        for body in rules.get(selector, []):
            if re.search(rf'{prop}\s*:\s*{value}', body):
                found = True
                break
        # Also check compound selectors containing our selector
        if not found:
            for sel, bodies in rules.items():
                if selector in sel and ',' not in sel.split(selector)[0]:
                    for body in bodies:
                        if re.search(rf'{prop}\s*:\s*{value}', body):
                            found = True
                            break
        results.append({'type': 'required', 'selector': selector, 'prop': prop, 'desc': desc, 'found': found})

    # Forbidden patterns
    for pattern, desc in FORBIDDEN_PATTERNS:
        match = re.search(pattern, css, re.DOTALL)
        results.append({'type': 'forbidden', 'pattern': pattern, 'desc': desc, 'violated': bool(match)})
    return results


def _strip_strings_and_comments(src: str) -> str:
    """Remove comments and string literals for bracket counting."""
    # Remove single-line comments (not inside strings - approximation)
    src = re.sub(r'(?<!:)\/\/[^\n]*', '', src)
    # Remove multi-line comments
    src = re.sub(r'/\*.*?\*/', '', src, flags=re.DOTALL)
    # Remove string literals
    src = re.sub(r"'(?:[^'\\]|\\.)*'", "''", src)
    src = re.sub(r'"(?:[^"\\]|\\.)*"', '""', src)
    # Remove template literals (handle nested ${} by keeping the backticks but removing content)
    src = re.sub(r'`(?:[^`\\]|\\.)*`', '``', src, flags=re.DOTALL)
    return src


def check_js_syntax(js_files: list[pathlib.Path]) -> list[dict]:
    """Basic JS syntax check: bracket/brace/paren balance after stripping strings/comments.
    Tolerance of +/-2 to account for regex literals and complex template nesting."""
    results = []
    TOLERANCE = 2
    for f in js_files:
        src = read_file(f)
        cleaned = _strip_strings_and_comments(src)
        issues = []
        for open_c, close_c in [('{', '}'), ('(', ')'), ('[', ']')]:
            o = cleaned.count(open_c)
            c = cleaned.count(close_c)
            diff = o - c
            if abs(diff) > TOLERANCE:
                issues.append(f"unbalanced {open_c}{close_c}: {o} open vs {c} close (diff={diff})")
        results.append({'file': f.name, 'issues': issues, 'ok': len(issues) == 0})
    return results


def check_a11y(html: str, css: str) -> list[dict]:
    """Check buttons have labels; focus styles exist."""
    results = []
    # Buttons with empty text and no aria-label
    btn_pattern = re.compile(r'<button([^>]*)>(.*?)</button>', re.DOTALL)
    unlabeled = []
    for m in btn_pattern.finditer(html):
        attrs, inner = m.group(1), m.group(2).strip()
        has_aria = 'aria-label' in attrs
        if not inner and not has_aria:
            unlabeled.append(attrs.strip()[:50])
    results.append({'check': 'unlabeled_buttons', 'count': len(unlabeled), 'details': unlabeled})
    # Focus-visible styles
    has_focus = ':focus' in css or ':focus-visible' in css
    results.append({'check': 'focus_styles_exist', 'found': has_focus})
    return results


def check_viewport_layout(html: str, css: str, vw: int) -> list[dict]:
    """Check that at a given viewport width, no critical element is clipped.
    Static heuristic: look for media queries that hide/hide-overflow at this width."""
    results = []
    # Find media queries that apply at this width
    mq_pattern = re.compile(r'@media[^{]*min-width\s*:\s*(\d+)px[^{]*\{|@media[^{]*max-width\s*:\s*(\d+)px')
    active_mqs = []
    for m in re.finditer(r'@media\s*\(([^)]+)\)\s*\{', css):
        cond = m.group(1)
        # Simple evaluation: if max-width >= vw or min-width <= vw, it might apply
        mm = re.search(r'max-width\s*:\s*(\d+)', cond)
        mn = re.search(r'min-width\s*:\s*(\d+)', cond)
        applies = True
        if mm and int(mm.group(1)) < vw:
            applies = False
        if mn and int(mn.group(1)) > vw:
            applies = False
        if applies:
            active_mqs.append(cond)
    results.append({'viewport': vw, 'active_media_queries': len(active_mqs)})
    # Check that .seg buttons are not hidden at this width
    seg_hidden = re.search(r'\.seg\s*\{[^}]*display\s*:\s*none', css)
    if seg_hidden:
        results.append({'viewport': vw, 'issue': '.seg display:none found'})
    return results


def run_full_check() -> dict:
    """Run all checks and return a report."""
    t0 = time.time()
    html = read_file(INDEX_HTML)
    css_files = sorted(UI_DIR.glob('*.css')) if UI_DIR.exists() else []
    # Use the canonical app.css + tokens.css
    app_css = read_file(UI_DIR / 'app.css')
    tokens_css = read_file(UI_DIR / 'tokens.css')
    full_css = app_css + '\n' + tokens_css
    js_files = sorted(f for f in UI_DIR.glob('*.js')) if UI_DIR.exists() else []

    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'checks': {},
    }
    # 1. Panels
    report['checks']['panels'] = check_panels(html)
    # 2. CSS layout
    report['checks']['css'] = check_css(full_css)
    # 3. JS syntax
    report['checks']['js_syntax'] = check_js_syntax(js_files)
    # 4. A11y
    report['checks']['a11y'] = check_a11y(html, full_css)
    # 5. Viewport layout (heuristic)
    for vw in VIEWPORTS:
        report['checks'].setdefault('viewports', []).extend(check_viewport_layout(html, full_css, vw))

    # Summary
    all_pass = True
    for p in report['checks']['panels']:
        if not p['found']:
            all_pass = False
    for c in report['checks']['css']:
        if c['type'] == 'required' and not c['found']:
            all_pass = False
        if c['type'] == 'forbidden' and c.get('violated'):
            all_pass = False
    for j in report['checks']['js_syntax']:
        if not j['ok']:
            all_pass = False
    for a in report['checks']['a11y']:
        if a['check'] == 'unlabeled_buttons' and a['count'] > 0:
            all_pass = False
        if a['check'] == 'focus_styles_exist' and not a['found']:
            all_pass = False

    report['overall_pass'] = all_pass
    report['duration_ms'] = round((time.time() - t0) * 1000, 1)
    return report


def self_test() -> dict:
    """Run built-in tests with synthetic inputs."""
    results = []

    # T1: Panel detection - all panels found
    html_ok = '<div id="modeBar"></div><div id="goalBar"></div><div id="fleetPanel"></div>'
    r = check_panels(html_ok)
    assert all(p['found'] for p in r), f"T1 fail: {r}"
    results.append({'test': 'T1_panels_all_found', 'pass': True})

    # T2: Panel detection - missing panel caught
    html_bad = '<div id="modeBar"></div>'
    r = check_panels(html_bad)
    assert any(not p['found'] for p in r), "T2 fail: should detect missing panels"
    results.append({'test': 'T2_panels_missing_detected', 'pass': True})

    # T3: CSS required props - present
    css_ok = '.seg{display:flex;flex:none;border-radius:4px} .toggles{display:inline-flex;flex:none}'
    r = check_css(css_ok)
    req_results = [x for x in r if x['type'] == 'required']
    assert all(x['found'] for x in req_results), f"T3 fail: {req_results}"
    results.append({'test': 'T3_css_required_present', 'pass': True})

    # T4: CSS required props - missing detected
    css_bad = '.seg{display:flex;flex:1}'
    r = check_css(css_bad)
    req_results = [x for x in r if x['type'] == 'required']
    assert any(not x['found'] for x in req_results), "T4 fail: should detect missing rules"
    results.append({'test': 'T4_css_required_missing', 'pass': True})

    # T5: CSS forbidden pattern - overflow:hidden on #modeBar caught
    css_forbidden = '#modeBar{overflow:hidden;display:flex}'
    r = check_css(css_forbidden)
    forb_results = [x for x in r if x['type'] == 'forbidden']
    assert any(x.get('violated') for x in forb_results), f"T5 fail: {forb_results}"
    results.append({'test': 'T5_css_forbidden_detected', 'pass': True})

    # T6: JS syntax - clean file passes
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tf:
        tf.write('function hello() { return "world"; }\nconst x = [1,2,3];\n')
        tmp_path = tf.name
    r = check_js_syntax([pathlib.Path(tmp_path)])
    assert r[0]['ok'], f"T6 fail: {r}"
    os.unlink(tmp_path)
    results.append({'test': 'T6_js_clean_passes', 'pass': True})

    # T7: JS syntax - significantly unbalanced braces caught
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tf:
        tf.write('function broken() { if (x) { return 1; } else { { {\n')  # 4 open vs 2 close = diff 2... need more
        tmp_path = tf.name
    r = check_js_syntax([pathlib.Path(tmp_path)])
    assert not r[0]['ok'], f"T7 fail: should detect unbalanced braces: {r}"
    os.unlink(tmp_path)
    results.append({'test': 'T7_js_unbalanced_detected', 'pass': True})

    # T8: A11y - unlabeled button caught
    html_btn = '<button class="icon"></button>'  # empty, no aria-label
    r = check_a11y(html_btn, ':focus{outline:2px solid blue}')
    btn_check = [x for x in r if x['check'] == 'unlabeled_buttons'][0]
    assert btn_check['count'] == 1, f"T8 fail: {btn_check}"
    results.append({'test': 'T8_a11y_unlabeled_button', 'pass': True})

    # T9: A11y - labeled button passes
    html_btn_ok = '<button aria-label="Close">✕</button>'
    r = check_a11y(html_btn_ok, ':focus{outline:2px solid blue}')
    btn_check = [x for x in r if x['check'] == 'unlabeled_buttons'][0]
    assert btn_check['count'] == 0, f"T9 fail: {btn_check}"
    results.append({'test': 'T9_a11y_labeled_passes', 'pass': True})

    # T10: Viewport check - .seg display:none at narrow width caught
    css_vw = '@media (max-width: 800px) { .seg{display:none} }'
    r = check_viewport_layout('', css_vw, 768)
    issues = [x for x in r if 'issue' in x]
    assert len(issues) == 1, f"T10 fail: {r}"
    results.append({'test': 'T10_viewport_seg_hidden_caught', 'pass': True})

    passed = sum(1 for r in results if r['pass'])
    return {'total': len(results), 'passed': passed, 'failed': len(results) - passed, 'results': results}


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        report = self_test()
        print(json.dumps(report, indent=2))
        sys.exit(0 if report['failed'] == 0 else 1)
    else:
        report = run_full_check()
        # Write results
        out = pathlib.Path(__file__).parent / 'ui_static_gate_results.json'
        out.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps({k: v for k, v in report.items() if k != 'checks'}, indent=2))
        # Print failures
        for p in report['checks']['panels']:
            if not p['found']:
                print(f"  MISSING PANEL: {p['panel']}")
        for c in report['checks']['css']:
            if c['type'] == 'required' and not c['found']:
                print(f"  CSS PROP MISSING: {c['selector']} needs {c['prop']} ({c['desc']})")
            if c['type'] == 'forbidden' and c.get('violated'):
                print(f"  CSS FORBIDDEN: {c['pattern']}")
        for j in report['checks']['js_syntax']:
            if not j['ok']:
                print(f"  JS SYNTAX ERROR in {j['file']}: {'; '.join(j['issues'])}")
        for a in report['checks']['a11y']:
            if a['check'] == 'unlabeled_buttons' and a['count'] > 0:
                print(f"  A11Y: {a['count']} unlabeled button(s): {a['details'][:3]}")
        sys.exit(0 if report['overall_pass'] else 1)
