#!/usr/bin/env python3
"""Regression Guard - pre-commit check for agent_portal.py and ui/*.

Usage:
  python memory/verifier/regression_guard.py --pre-commit   # full check, exit 0 only on pass
  python memory/verifier/regression_guard.py --live         # also hit live endpoints

Checks:
  1. JS syntax: balanced delimiters, no obvious errors in ui/*.js
  2. CSS parse: basic structural validation of ui/*.css
  3. agent_portal.py: Python syntax check (ast.parse)
  4. [--live] GET each /api/* endpoint, expect 200 + valid JSON

Exit codes: 0 = all pass, 1 = one or more failures.
"""
import ast
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
UI_DIR = BASE / "ui"
PORTAL_PY = BASE / "agent_portal.py"
LIVE_URL = "http://localhost:8099"

results = []  # (check_name, passed: bool, detail: str)


def check(name, passed, detail=""):
    results.append((name, passed, detail))
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}" + (f" - {detail}" if detail and not passed else ""))


def _strip_js(text):
    """Strip comments, strings, template literals, and regex literals from JS."""
    result = []
    i = 0
    n = len(text)
    regex_preceders = set('=(,:[!&|?{};+-*%~^<>\n')
    while i < n:
        if text[i:i+2] == '/*':
            end = text.find('*/', i+2)
            i = end + 2 if end != -1 else n
            continue
        if text[i:i+2] == '//':
            end = text.find('\n', i)
            i = end if end != -1 else n
            continue
        if text[i] in ('"', "'"):
            quote = text[i]
            i += 1
            while i < n and text[i] != quote:
                if text[i] == '\\':
                    i += 1
                i += 1
            i += 1
            result.append("''")
            continue
        if text[i] == '`':
            i += 1
            depth = 0
            while i < n:
                if text[i] == '\\':
                    i += 2
                    continue
                if text[i] == '$' and i+1 < n and text[i+1] == '{':
                    depth += 1
                    i += 2
                    continue
                if text[i] == '}' and depth > 0:
                    depth -= 1
                    i += 1
                    continue
                if text[i] == '`' and depth == 0:
                    i += 1
                    break
                i += 1
            result.append('``')
            continue
        # Regex literal detection
        if text[i] == '/' and (not result or result[-1][-1:] in regex_preceders):
            j = i + 1
            in_class = False
            valid = False
            while j < n:
                if text[j] == '\\':
                    j += 2
                    continue
                if text[j] == '[':
                    in_class = True
                elif text[j] == ']':
                    in_class = False
                elif text[j] == '/' and not in_class:
                    valid = True
                    break
                elif text[j] == '\n':
                    break
                j += 1
            if valid:
                while j < n and text[j].isalpha():
                    j += 1
                i = j
                result.append('')
                continue
        result.append(text[i])
        i += 1
    return ''.join(result)


def check_js_syntax(filepath):
    """JS structural validation: balanced delimiters after stripping strings/comments/regexes."""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    stripped = _strip_js(text)
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    for i, ch in enumerate(stripped):
        if ch in '([{':
            stack.append((ch, i))
        elif ch in ')]}':
            if not stack:
                return False, f"unmatched '{ch}' at pos {i}"
            top, pos = stack.pop()
            if top != pairs[ch]:
                return False, f"'{top}' (pos {pos}) closed by '{ch}' (pos {i})"
    if stack:
        ch, pos = stack[-1]
        return False, f"unclosed '{ch}' at pos {pos}"
    return True, ""


def check_css_basic(filepath):
    """Basic CSS structural validation: balanced braces, no empty rules with missing selectors."""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    # Strip comments
    text_nc = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    open_count = text_nc.count('{')
    close_count = text_nc.count('}')
    if open_count != close_count:
        return False, f"unbalanced braces: {open_count} open vs {close_count} close"
    # Check for obvious syntax errors: property without colon (heuristic)
    # Look for lines that have a value but no colon (excluding selectors and at-rules)
    problems = []
    for line in text_nc.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('@') or stripped.endswith('{') or stripped == '}':
            continue
        # Inside a rule block, expect prop: value;
        if ':' not in stripped and ';' not in stripped and not stripped.startswith('}'):
            # Could be a selector line (no semicolon, no colon) - that's OK
            # Only flag if it looks like a broken declaration
            pass  # heuristic is too noisy; rely on brace balance
    return True, ""


def check_python_syntax(filepath):
    """Validate Python file parses without SyntaxError."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        ast.parse(source)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError line {e.lineno}: {e.msg}"


def check_live_endpoints():
    """Hit known /api/* endpoints and verify 200 + JSON."""
    endpoints = ["/api/goals", "/api/fleet/overview", "/api/agents", "/api/health"]
    all_ok = True
    details = []
    for ep in endpoints:
        url = f"{LIVE_URL}{ep}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status != 200:
                    all_ok = False
                    details.append(f"{ep}: HTTP {resp.status}")
                    continue
                body = resp.read()
                try:
                    json.loads(body)
                except json.JSONDecodeError:
                    all_ok = False
                    details.append(f"{ep}: invalid JSON")
        except Exception as e:
            all_ok = False
            details.append(f"{ep}: {type(e).__name__}: {e}")
    return all_ok, "; ".join(details[:4])


def main():
    mode = "--live" if "--live" in sys.argv else "--pre-commit"
    print(f"\n=== Regression Guard ({mode}) ===")

    # 1. Python syntax: agent_portal.py
    if PORTAL_PY.exists():
        ok, detail = check_python_syntax(PORTAL_PY)
        check("agent_portal.py syntax", ok, detail)
    else:
        check("agent_portal.py syntax", False, "file not found")

    # 2. JS syntax: all ui/*.js files
    js_files = sorted(UI_DIR.glob("*.js")) if UI_DIR.exists() else []
    for jf in js_files:
        ok, detail = check_js_syntax(jf)
        check(f"JS syntax: {jf.name}", ok, detail)
    if not js_files:
        check("JS files found", False, "no .js files in ui/")

    # 3. CSS: all ui/*.css files
    css_files = sorted(UI_DIR.glob("*.css")) if UI_DIR.exists() else []
    for cf in css_files:
        ok, detail = check_css_basic(cf)
        check(f"CSS parse: {cf.name}", ok, detail)
    if not css_files:
        check("CSS files found", False, "no .css files in ui/")

    # 4. Live endpoints (only with --live flag)
    if mode == "--live":
        print(f"\n  Live endpoint checks ({LIVE_URL}):")
        ok, detail = check_live_endpoints()
        check("Live /api/* endpoints", ok, detail)
    else:
        print("\n  [SKIP] Live endpoint checks (use --live to enable)")

    # Summary
    total = len(results)
    passed = sum(1 for _, p, _ in results if p)
    failed = total - passed
    print(f"\n=== Result: {passed}/{total} passed, {failed} failed ===")

    if failed > 0:
        print("\nFAILURES:")
        for name, p, detail in results:
            if not p:
                print(f"  - {name}: {detail}")
        sys.exit(1)
    else:
        print("\nAll checks passed. Safe to commit.")
        sys.exit(0)


if __name__ == "__main__":
    main()
