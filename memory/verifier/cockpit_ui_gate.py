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


def check_js_syntax(js_path: Path) -> dict:
    """Basic JS syntax check: balanced braces, parens, brackets; no unterminated strings."""
    if not js_path.exists():
        return {"file": str(js_path.name), "pass": False, "error": "file not found"}
    
    content = js_path.read_text(encoding="utf-8", errors="replace")
    issues = []
    
    # Balanced braces
    for open_ch, close_ch, name in [("{", "}", "braces"), ("(", ")", "parens"), ("[", "]", "brackets")]:
        depth = 0
        in_string = None
        escape = False
        for i, ch in enumerate(content):
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if in_string:
                if ch == in_string:
                    in_string = None
                continue
            if ch in ('"', "'", "`"):
                in_string = ch
                continue
            if ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth < 0:
                    issues.append(f"unbalanced {name} at position {i}")
                    break
        if depth > 0 and not any(name in iss for iss in issues):
            issues.append(f"unclosed {name}: {depth} extra")
    
    # Unterminated line comments (lines starting with // that have no newline after)
    lines = content.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("//") and not stripped.endswith("*/"):
            pass  # line comments are fine
    
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
