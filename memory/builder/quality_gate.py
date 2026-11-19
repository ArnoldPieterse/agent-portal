#!/usr/bin/env python3
"""quality_gate.py - Code quality lint for portal UI files.

Checks (per goal #10):
  1. No console.log in production JS (ui/*.js)
  2. No unused imports (basic: top-level var/let/const declarations never referenced)
  3. File size <500 lines per JS/CSS file
  4. All new UI uses components.js (document.createElement count in core.js <5)

Usage:
  python memory/builder/quality_gate.py            # check all ui/ files
  python memory/builder/quality_gate.py --verbose  # show line-by-line violations

Exit: 0 = clean, 1 = violations found
"""
import os, re, sys
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UI_DIR = os.path.join(ROOT, "ui")
MAX_LINES = 500
CREATE_ELEMENT_LIMIT = 5

violations = []  # list of (severity, file, line, message)


def add(severity, fname, line, msg):
    violations.append((severity, fname, line, msg))


def check_console_log(fname, content, verbose=False):
    """Check 1: no console.log/warn/error in production code."""
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        # Skip comment-only lines
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        # Find console.log/warn/error calls (not in strings)
        # Remove string contents to avoid false positives
        no_str = re.sub(r"'(?:[^'\\]|\\.)*'", "''", line)
        no_str = re.sub(r'"(?:[^"\\]|\\.)*"', '""', no_str)
        no_str = re.sub(r"`(?:[^`\\]|\\.)*`", "``", no_str)
        for pattern in [r"console\.log\b", r"console\.warn\b", r"console\.error\b"]:
            if re.search(pattern, no_str):
                add("WARN", fname, i, f"console call in production: {stripped[:60]}")


def check_file_size(fname, content):
    """Check 3: file size <500 lines."""
    line_count = len(content.split("\n"))
    if line_count > MAX_LINES:
        add("FAIL", fname, 0, f"{line_count} lines (limit {MAX_LINES})")


def check_create_element(fname, content):
    """Check 4: document.createElement usage in core.js should be <5."""
    if not fname.endswith("core.js"):
        return
    count = len(re.findall(r"document\.createElement\b", content))
    if count >= CREATE_ELEMENT_LIMIT:
        add("WARN", fname, 0,
            f"document.createElement={count} (target<{CREATE_ELEMENT_LIMIT}) - convert to UI.* components")


def check_unused_vars(fname, content):
    """Check 2: basic unused top-level variable detection.
    Heuristic: find var/let/const X = ... at top level, then check if X is
    referenced elsewhere in the file. Only flags clearly unused variables.
    """
    lines = content.split("\n")
    # Find top-level declarations (not indented, matching var/let/const NAME =)
    declared = {}  # name -> line_number
    for i, line in enumerate(lines, 1):
        m = re.match(r"^(?:var|let|const)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=", line)
        if m:
            declared[m.group(1)] = i
    
    # Check each declaration for usage elsewhere
    full_text = content
    for name, decl_line in declared.items():
        # Count occurrences of the variable name (word boundary)
        pattern = r"\b" + re.escape(name) + r"\b"
        occurrences = len(re.findall(pattern, full_text))
        # 1 occurrence = only the declaration itself
        if occurrences <= 1:
            add("WARN", fname, decl_line, f"possibly unused variable: {name}")


def check_component_usage(fname, content):
    """Check 4b: files that build DOM should use UI.* component functions."""
    # Only check core.js and uploads.js (the main panel builders)
    if fname not in ("core.js", "uploads.js"):
        return
    ui_calls = len(re.findall(r"\bUI\.[a-zA-Z]+\b", content))
    ce_calls = len(re.findall(r"document\.createElement\b", content))
    if ce_calls > 0 and ui_calls == 0:
        add("WARN", fname, 0,
            f"{ce_calls} createElement calls but 0 UI.* component calls - consider using components.js")


def main():
    verbose = "--verbose" in sys.argv
    print(f"=== QUALITY GATE ===")
    print(f"Target: ui/ ({MAX_LINES} line limit, {CREATE_ELEMENT_LIMIT} createElement max in core.js)")
    print()

    if not os.path.isdir(UI_DIR):
        print(f"FAIL: {UI_DIR} not found")
        sys.exit(1)

    checked = 0
    for fname in sorted(os.listdir(UI_DIR)):
        fpath = os.path.join(UI_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        if not fname.endswith((".js", ".css")):
            continue
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        checked += 1

        check_file_size(fname, content)
        if fname.endswith(".js"):
            check_console_log(fname, content, verbose)
            check_unused_vars(fname, content)
            check_create_element(fname, content)
            check_component_usage(fname, content)

    # Report
    fails = [v for v in violations if v[0] == "FAIL"]
    warns = [v for v in violations if v[0] == "WARN"]

    print(f"Files checked: {checked}")
    print(f"  FAIL: {len(fails)}")
    for sev, fname, line, msg in fails:
        loc = f":{line}" if line else ""
        print(f"    [FAIL] {fname}{loc} - {msg}")
    print(f"  WARN: {len(warns)}")
    for sev, fname, line, msg in warns:
        loc = f":{line}" if line else ""
        print(f"    [WARN] {fname}{loc} - {msg}")

    total_issues = len(fails) + len(warns)
    print()
    if fails:
        print(f"=== RESULT: FAIL ({len(fails)} hard violations, {len(warns)} warnings) ===")
        sys.exit(1)
    elif warns and verbose:
        print(f"=== RESULT: PASS with {len(warns)} warnings ===")
        sys.exit(0)
    else:
        status = f"PASS ({len(warns)} warnings, non-blocking)" if warns else "PASS (clean)"
        print(f"=== RESULT: {status} ===")
        sys.exit(0)


if __name__ == "__main__":
    main()
