"""Cockpit UI Gate — static structural verification of cockpit panels + JS + interactivity.

Best-available alternative to full Playwright browser test when no browser is available.
Checks:
  1. HTML: expected panel containers exist (by ID/class)
  2. JS files: syntactically valid (balanced braces/parens, no unterminated strings)
  3. CSS file: loads and has non-zero content
  4. Interactive elements: buttons/links with event handlers present
  5. Viewport meta tag present (responsive support)

Usage:
  python memory/verifier/cockpit_ui_gate.py --self-test
  python memory/verifier/cockpit_ui_gate.py

NOTE: Full Playwright browser test (rendering, JS runtime errors, click interaction)
requires a host with `playwright install chromium`. This static gate covers structure
and syntax but NOT runtime behavior.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent  # project root (3 levels up from memory/verifier/)
UI_DIR = BASE / "ui"
INDEX_HTML = BASE / "index.html"


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_html_structure(html: str) -> dict:
    """Check that expected cockpit panels/containers exist in HTML."""
    # Expected panel IDs/classes (from cockpit design)
    expected_elements = [
        ("div", "cockpit"),  # main cockpit container
        ("div", "fleet-panel"),  # fleet status panel
        ("div", "goals-panel"),  # goals panel
        ("div", "health-panel"),  # health score panel
    ]
    
    found = []
    missing = []
    for tag, identifier in expected_elements:
        # Check by id or class
        pattern_id = f'id="{identifier}"'
        pattern_class = f'class="[^"]*{identifier}[^"]*"'
        if re.search(pattern_id, html) or re.search(pattern_class, html):
            found.append(identifier)
        else:
            missing.append(identifier)
    
    # Check viewport meta
    has_viewport = bool(re.search(r'<meta[^>]*name="viewport"', html))
    
    return {
        "check": "html_structure",
        "expected_elements": len(expected_elements),
        "found": found,
        "missing": missing,
        "has_viewport_meta": has_viewport,
        "pass": len(missing) == 0 and has_viewport,
    }


def _js_scan_issues(content: str):
    """Stateful mini-scanner that returns a list of real JS balance problems.

    Unlike a naive brace counter it tracks lexical state so that the *contents*
    of strings, comments, template literals and regex literals do not corrupt
    bracket balance. Handles: // and /* */ comments; '...' and "..." strings with
    backslash escapes; `...` template literals INCLUDING ${ ... } interpolation
    (nested templates/strings inside interpolations); and /.../ regex literals
    (character classes, quantifiers, and a division-vs-regex heuristic based on
    the preceding significant token). A non-empty result means a genuine defect
    (unbalanced bracket or unterminated string/template), not a false positive.
    """
    n = len(content); i = 0; line = 1
    CODE = 'code'; TPL = 'template'
    NORM = 'norm'; LC = 'lc'; BC = 'bc'; SS = 'ss'; DS = 'ds'; RX = 'rx'
    stack = [{'kind': CODE, 'b': 0, 'p': 0, 'k': 0}]  # root code frame
    mode = NORM; prev_sig = None; issues = []

    def top(): return stack[-1]

    while i < n:
        ch = content[i]; nxt = content[i + 1] if i + 1 < n else ''
        if ch == '\n': line += 1
        ctx = top()
        # -- template literal text region (skip until ` or ${ ) --
        if ctx['kind'] == TPL:
            if mode == NORM:
                if ch == '\\': i += 2; continue
                if ch == '`': stack.pop(); i += 1; continue
                if ch == '$' and nxt == '{':
                    stack.append({'kind': CODE, 'b': 0, 'p': 0, 'k': 0}); mode = NORM; i += 2; continue
                i += 1; continue
            i += 1; continue
        # -- transient lexical modes within a code frame --
        if mode == LC:
            if ch == '\n': mode = NORM
            i += 1; continue
        if mode == BC:
            if ch == '*' and nxt == '/': mode = NORM; i += 2; continue
            i += 1; continue
        if mode in (SS, DS):
            q = "'" if mode == SS else '"'
            if ch == '\\': i += 2; continue
            if ch == '\n': issues.append("unterminated string at line %d" % line); mode = NORM; i += 1; continue
            if ch == q: mode = NORM; prev_sig = 'close'
            i += 1; continue
        if mode == RX:
            if ch == '\\': i += 2; continue
            if ch == '\n': mode = NORM; prev_sig = 'other'; i += 1; continue
            if ch == '[':  # character class: skip to unescaped ]
                j = i + 1
                if j < n and content[j] == '^': j += 1
                if j < n and content[j] == ']': j += 1
                while j < n and content[j] != ']':
                    if content[j] == '\\': j += 1
                    j += 1
                i = j + 1; continue
            if ch == '/': mode = NORM; prev_sig = 'close'; i += 1; continue
            i += 1; continue
        # -- normal code --
        if ch == '/' and nxt == '/': mode = LC; i += 2; continue
        if ch == '/' and nxt == '*': mode = BC; i += 2; continue
        if ch == "'": mode = SS; prev_sig = 'close'; i += 1; continue
        if ch == '"': mode = DS; prev_sig = 'close'; i += 1; continue
        if ch == '`': stack.append({'kind': TPL}); mode = NORM; i += 1; continue
        if ch == '/':
            # division if the previous significant token ends a value, else regex
            if prev_sig in ('ident', 'num', 'close'):
                prev_sig = 'other'; i += 1; continue
            mode = RX; prev_sig = None; i += 1; continue
        if ch == '{': ctx['b'] += 1; prev_sig = 'other'
        elif ch == '}':
            if ctx['kind'] == CODE and ctx['b'] == 0 and len(stack) > 1:
                stack.pop(); mode = NORM; i += 1; continue  # closes ${ } interpolation
            ctx['b'] -= 1
            if ctx['b'] < 0 and len(stack) == 1: issues.append("unbalanced braces at line %d" % line)
            prev_sig = 'close'
        elif ch == '(':
            ctx['p'] += 1; prev_sig = 'other'
        elif ch == ')':
            ctx['p'] -= 1
            if ctx['p'] < 0 and len(stack) == 1: issues.append("unbalanced parens at line %d" % line)
            prev_sig = 'close'
        elif ch == '[':
            ctx['k'] += 1; prev_sig = 'other'
        elif ch == ']':
            ctx['k'] -= 1
            if ctx['k'] < 0 and len(stack) == 1: issues.append("unbalanced brackets at line %d" % line)
            prev_sig = 'close'
        else:
            if ch.isalnum() or ch == '_' or ch == '$': prev_sig = 'ident'
            elif not ch.isspace(): prev_sig = 'other'
        i += 1; continue

    root = stack[0]
    for key, name in (('b', 'braces'), ('p', 'parens'), ('k', 'brackets')):
        if root[key] > 0: issues.append("unclosed %s: %d extra" % (name, root[key]))
    if len(stack) > 1:
        issues.append("unterminated template/string at line %d" % line)
    return issues


def check_js_syntax(js_path: Path) -> dict:
    """JS syntax check via _js_scan_issues (string/comment/template/regex aware).
    Returns {file, size_bytes, issues, pass}; issues non-empty => real defect."""
    if not js_path.exists():
        return {"file": str(js_path.name), "pass": False, "error": "file not found"}

    content = js_path.read_text(encoding="utf-8", errors="replace")
    issues = _js_scan_issues(content)

    return {
        "file": js_path.name,
        "size_bytes": len(content),
        "issues": issues,
        "pass": len(issues) == 0,
    }


def check_css(css_path: Path) -> dict:
    """Check CSS file exists and has meaningful content."""
    if not css_path.exists():
        return {"file": str(css_path.name), "pass": False, "error": "file not found"}
    
    content = css_path.read_text(encoding="utf-8", errors="replace")
    # Count rule blocks (rough: count { ... } pairs)
    rule_count = content.count("{")
    
    return {
        "file": css_path.name,
        "size_bytes": len(content),
        "rule_blocks": rule_count,
        "pass": len(content) > 100 and rule_count > 5,
    }


def check_interactive_elements(html: str) -> dict:
    """Check that interactive elements (buttons, links with handlers) exist."""
    buttons = re.findall(r'<button[^>]*>', html)
    links_with_handlers = re.findall(r'<a[^>]*(?:onclick|data-action)[^>]*>', html)
    inputs = re.findall(r'<input[^>]*>', html)
    
    total_interactive = len(buttons) + len(links_with_handlers) + len(inputs)
    
    return {
        "check": "interactive_elements",
        "buttons": len(buttons),
        "links_with_handlers": len(links_with_handlers),
        "inputs": len(inputs),
        "total": total_interactive,
        "pass": total_interactive > 0,
    }


def run_gate() -> dict:
    """Run the full static UI gate."""
    results = {"ts": now_iso(), "checks": [], "overall_pass": True}
    
    # Check HTML exists
    if not INDEX_HTML.exists():
        results["checks"].append({"check": "html_exists", "pass": False, "error": f"{INDEX_HTML} not found"})
        results["overall_pass"] = False
        return results
    
    html = INDEX_HTML.read_text(encoding="utf-8", errors="replace")
    
    # Check 1: HTML structure
    r1 = check_html_structure(html)
    results["checks"].append(r1)
    if not r1["pass"]:
        results["overall_pass"] = False
    
    # Check 2: JS files syntax
    js_results = []
    for js_file in UI_DIR.glob("*.js") if UI_DIR.exists() else []:
        r = check_js_syntax(js_file)
        js_results.append(r)
        if not r["pass"]:
            results["overall_pass"] = False
    results["checks"].append({"check": "js_syntax", "files_checked": len(js_results), "results": js_results, "pass": all(r["pass"] for r in js_results)})
    
    # Check 3: CSS
    css_files = list(UI_DIR.glob("*.css")) if UI_DIR.exists() else []
    css_results = [check_css(f) for f in css_files]
    results["checks"].append({"check": "css", "files_checked": len(css_results), "results": css_results, "pass": all(r["pass"] for r in css_results)})
    
    # Check 4: Interactive elements
    r4 = check_interactive_elements(html)
    results["checks"].append(r4)
    if not r4["pass"]:
        results["overall_pass"] = False
    
    return results


def self_test():
    """Self-test with synthetic HTML to prove both pass and fail branches."""
    print("=== Cockpit UI Gate Self-Test ===")
    passed = 0
    failed = 0
    
    # T1: Valid HTML passes structure check
    print("\nT1: Valid cockpit HTML -> structure check passes")
    valid_html = """<html><head><meta name="viewport" content="width=device-width"></head>
    <body>
      <div id="cockpit">
        <div class="fleet-panel">Fleet</div>
        <div class="goals-panel">Goals</div>
        <div class="health-panel">Health</div>
      </div>
      <button onclick="doThing()">Click me</button>
    </body></html>"""
    r = check_html_structure(valid_html)
    if r["pass"] and len(r["found"]) == 4:
        print(f"  PASS: all 4 elements found, viewport present")
        passed += 1
    else:
        print(f"  FAIL: {r}")
        failed += 1
    
    # T2: Missing panels fail structure check
    print("\nT2: HTML missing panels -> structure check fails")
    bad_html = "<html><body><div id='cockpit'>only cockpit</div></body></html>"
    r = check_html_structure(bad_html)
    if not r["pass"] and len(r["missing"]) >= 3:
        print(f"  PASS: {len(r['missing'])} missing detected")
        passed += 1
    else:
        print(f"  FAIL: {r}")
        failed += 1
    
    # T3: Balanced JS passes syntax check
    print("\nT3: Valid JS file -> syntax check passes")
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write("function test() { return (1 + 2) * [3][0]; }\nconsole.log(test());\n")
        js_path = f.name
    r = check_js_syntax(Path(js_path))
    if r["pass"]:
        print(f"  PASS: balanced JS passes")
        passed += 1
    else:
        print(f"  FAIL: {r}")
        failed += 1
    import os; os.unlink(js_path)
    
    # T4: Unbalanced JS fails syntax check
    print("\nT4: Unbalanced JS -> syntax check fails")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write("function broken() { if (x > 0) {\nreturn x;\n}\n// missing closing brace\n")
        js_path = f.name
    r = check_js_syntax(Path(js_path))
    if not r["pass"] and len(r["issues"]) > 0:
        print(f"  PASS: issues detected: {r['issues']}")
        passed += 1
    else:
        print(f"  FAIL: expected issues but got pass")
        failed += 1
    os.unlink(js_path)
    
    # T5: Interactive elements detected
    print("\nT5: HTML with buttons -> interactive check passes")
    html_with_btn = "<html><body><button onclick='x()'>Go</button></body></html>"
    r = check_interactive_elements(html_with_btn)
    if r["pass"] and r["buttons"] >= 1:
        print(f"  PASS: {r['buttons']} button(s) found")
        passed += 1
    else:
        print(f"  FAIL: {r}")
        failed += 1
    
    # T6: Empty HTML -> interactive check fails
    print("\nT6: HTML with no interactive elements -> check fails")
    r = check_interactive_elements("<html><body><p>Static only</p></body></html>")
    if not r["pass"] and r["total"] == 0:
        print(f"  PASS: correctly detected 0 interactive elements")
        passed += 1
    else:
        print(f"  FAIL: {r}")
        failed += 1
    
    print(f"\n=== RESULTS: {passed} PASS / {failed} FAIL ===")
    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Cockpit UI Gate (static)")
    parser.add_argument("--self-test", action="store_true", help="Run built-in self-test")
    args = parser.parse_args()
    
    if args.self_test:
        sys.exit(self_test())
    
    result = run_gate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["overall_pass"] else 1)


if __name__ == "__main__":
    main()
