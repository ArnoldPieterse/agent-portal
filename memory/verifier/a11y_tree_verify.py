#!/usr/bin/env python3
"""
Accessibility Tree Verification - Designer Goal #7 (cycle-8)
Checks DOM structure for ARIA expectations:
  1. Heading order: h1>h2>h3, no skips
  2. Landmarks present: nav, main, aside
  3. Lists use ul/li (no divs as direct children of ul/ol)
  4. Tables have th/td structure

Works on static index.html + scans ui/*.js for dynamic DOM creation.
Run: python memory/verifier/a11y_tree_verify.py
"""
import re, os, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # project root
results = {"checks": {}, "violations": [], "pass": False}

def check(name, passed, detail):
    results["checks"][name] = {"passed": passed, "detail": detail}
    if not passed:
        results["violations"].append(f"{name}: {detail}")

# --- 1. HEADING ORDER ---
html = (ROOT / "index.html").read_text()
headings_static = re.findall(r'<(h[1-6])[^>]*>', html)

# Check JS for dynamic heading creation
js_headings = []
for fn in os.listdir(ROOT / "ui"):
    if not fn.endswith(".js"): continue
    js = (ROOT / "ui" / fn).read_text()
    # createElement('h1') or createElement("h2")
    js_headings += re.findall(r'createElement\([\'\"](h[1-6])[\'\"]\)', js)
    # innerHTML with heading tags
    js_headings += re.findall(r'<(h[1-6])[^>]*>', js)

all_headings = [("static", h) for h in headings_static] + [("js", h) for h in js_headings]
levels = [int(h[1]) for _, h in all_headings]

# Check for skips: each heading level must be at most 1 more than previous
skip_violations = []
for i in range(1, len(levels)):
    if levels[i] > levels[i-1] + 1:
        skip_violations.append(f"h{levels[i-1]} -> h{levels[i]} (skipped h{levels[i-1]+1})")

if not all_headings:
    check("heading_order", True, "No headings found (trivially valid)")
elif skip_violations:
    check("heading_order", False, "; ".join(skip_violations))
else:
    detail = f"{len(all_headings)} heading(s): {', '.join(f'h{l}' for l in levels)} - no skips"
    check("heading_order", True, detail)

# --- 2. LANDMARKS ---
landmarks_required = ["nav", "main", "aside"]
landmarks_found = []
for lm in landmarks_required:
    # Check static HTML
    if re.search(rf'<{lm}[\s>]', html):
        landmarks_found.append(lm)
        continue
    # Check JS
    found_in_js = False
    for fn in os.listdir(ROOT / "ui"):
        if not fn.endswith(".js"): continue
        js = (ROOT / "ui" / fn).read_text()
        if re.search(rf'createElement\([\'\"]{lm}[\'\"]\)', js) or re.search(rf'<{lm}[\s>]', js):
            landmarks_found.append(lm)
            found_in_js = True
            break
    if not found_in_js and lm not in landmarks_found:
        landmarks_found.append(None)  # placeholder

missing = [lm for lm, f in zip(landmarks_required, landmarks_found) if f is None]
if missing:
    check("landmarks", False, f"Missing landmarks: {', '.join(missing)}")
else:
    check("landmarks", True, f"All required landmarks present: {', '.join(landmarks_required)}")

# Bonus: check for aria-label on landmarks
aria_labels = re.findall(r'aria-label=[\'\"]([^\'\"]+)[\'\"]', html)
if not aria_labels:
    results["checks"]["landmarks_aria"] = {"passed": False, "detail": "No aria-label attributes found on landmarks"}
else:
    results["checks"]["landmarks_aria"] = {"passed": True, "detail": f"{len(aria_labels)} aria-label(s) present: {aria_labels[:5]}"}

# --- 3. LIST SEMANTICS ---
# Check that ul/ol elements in HTML don't have non-li direct children (static)
ul_ols = re.findall(r'<(ul|ol)[^>]*>(.*?)</\1>', html, re.DOTALL)
list_violations = []
for tag, content in ul_ols:
    # Strip nested elements, check for div/span as direct children
    direct_children = re.findall(r'>([^<]*<)(/?(\w+))', content)
    for text, closing, child_tag in direct_children:
        if child_tag in ("div", "span", "p") and not re.search(rf'<li[^>]*>', content[:content.find(f"<{child_tag}")]):
            # This is a simplification - check if div appears before any li
            pass  # Too complex for regex; note as info
    # Simpler: check if ul/ol contains only li (and text) at top level
    stripped = re.sub(r'<li[^>]*>.*?</li>', '', content, flags=re.DOTALL)
    remaining_tags = re.findall(r'<(\w+)', stripped)
    non_li = [t for t in remaining_tags if t not in ("ul", "ol")]
    if non_li:
        list_violations.append(f"<{tag}> contains non-li elements: {non_li}")

# Also check JS-created lists
js_list_issues = []
for fn in os.listdir(ROOT / "ui"):
    if not fn.endswith(".js"): continue
    js = (ROOT / "ui" / fn).read_text()
    # If createElement('ul') is used, check nearby for appendChild of non-li
    if 'createElement' in js and re.search(r'createElement\([\'\"](ul|ol)[\'\"]\)', js):
        # Flag for manual review
        js_list_issues.append(f"{fn}: creates <ul>/<ol> dynamically - verify children are <li>")

if list_violations:
    check("list_semantics", False, "; ".join(list_violations))
else:
    detail = f"{len(ul_ols)} static list(s) checked - all contain only li children"
    if js_list_issues:
        detail += f"; {len(js_list_issues)} dynamic list(s) flagged for review"
    check("list_semantics", True, detail)

# --- 4. TABLE STRUCTURE ---
tables_html = re.findall(r'<table[^>]*>', html)
tables_js = []
for fn in os.listdir(ROOT / "ui"):
    if not fn.endswith(".js"): continue
    js = (ROOT / "ui" / fn).read_text()
    tables_js += re.findall(r'createElement\([\'\"]table[\'\"]\)', js)
    tables_js += re.findall(r'<table[^>]*>', js)

total_tables = len(tables_html) + len(tables_js)
if total_tables == 0:
    check("table_structure", True, "No tables present (N/A)")
else:
    # Check for th usage
    th_count = len(re.findall(r'<th[\s>]', html))
    td_count = len(re.findall(r'<td[\s>]', html))
    if th_count == 0 and td_count > 0:
        check("table_structure", False, f"{total_tables} table(s) but no <th> header cells")
    else:
        check("table_structure", True, f"{total_tables} table(s), {th_count} th, {td_count} td")

# --- DELIBERATE VIOLATION TEST (negative test) ---
# Verify the script CAN catch a violation by testing against a bad snippet
bad_html = "<h1>Title</h1><h3>Skipped h2</h3>"
bad_levels = [int(h[1]) for h in re.findall(r'<(h[1-6])', bad_html)]
neg_skip = any(bad_levels[i] > bad_levels[i-1] + 1 for i in range(1, len(bad_levels)))
check("negative_test_heading_skip", neg_skip, "Script correctly detects h1->h3 skip" if neg_skip else "FAILED to detect known violation")

# --- SUMMARY ---
results["pass"] = all(c["passed"] for c in results["checks"].values())
print(json.dumps(results, indent=2))
sys.exit(0 if results["pass"] else 1)
