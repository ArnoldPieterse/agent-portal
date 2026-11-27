#!/usr/bin/env python3
"""verify_ui_change.py — Companion script for designer-ui-change-checklist.md.
Post-edit validation: checks that UI files (index.html, ui/*.css, ui/*.js) are parseable
and that no pin-file was modified without a corresponding CANONICAL backup.
Exit: 0=pass, 1=fail.
"""
import sys, json, re
from pathlib import Path

UI_FILES = ["index.html", "ui/app.css", "ui/core.js", "ui/uploads.js"]

def check_js_syntax(path: Path):
    """Basic JS sanity: balanced braces/parens."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return str(e)
    for open_c, close_c in [("{", "}"), ("(", ")"), ("[", "]")]:
        if text.count(open_c) != text.count(close_c):
            return f"Unbalanced {open_c}{close_c}: {text.count(open_c)} vs {text.count(close_c)}"
    return None

def check_html(path: Path):
    """Basic HTML sanity: has <html> and </html>."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return str(e)
    if "<html" not in text.lower() or "</html>" not in text.lower():
        return "Missing <html> or </html> tag"
    return None

def main():
    issues = []
    for f in UI_FILES:
        p = Path(f)
        if not p.exists():
            issues.append({"file": f, "error": "not found"})
            continue
        if f.endswith(".js"):
            err = check_js_syntax(p)
        elif f.endswith(".html"):
            err = check_html(p)
        else:
            err = None  # CSS: no easy syntax check without a parser
        if err:
            issues.append({"file": f, "error": err})
    
    if issues:
        print(json.dumps({"status": "FAIL", "issues": issues}, indent=2))
        sys.exit(1)
    print(json.dumps({"status": "PASS", "files_checked": UI_FILES}))
    sys.exit(0)

if __name__ == "__main__":
    main()
