#!/usr/bin/env python3
"""Goal 7: Accessibility Tree Verification
Checks DOM structure for ARIA compliance:
  - Heading order (no level skips)
  - Landmark presence (nav, main, aside, header)
  - List semantics (ul/li not divs styled as lists)
  - Table headers (th present in tables)

Usage: python memory/designer/a11y_tree_verify.py [html_file]
Exit 0 = pass, exit 1 = issues found.
"""
import re, json, sys, os

def verify_a11y_tree(html_path="index.html"):
    html = open(html_path, encoding="utf-8").read()
    results = {"heading_order": [], "landmarks": {}, "lists_ok": True, "tables_ok": True, "issues": []}

    # 1. Heading order check - no level skips (h1->h3 without h2 is a skip)
    headings = re.findall(r'<(h[1-6])[^>]*>(.*?)</\1>', html, re.DOTALL)
    prev = 0
    for tag, content in headings:
        lvl = int(tag[1])
        clean = re.sub(r'<[^>]+>', '', content).strip()[:80]
        entry = {"level": lvl, "text": clean}
        if prev > 0 and lvl > prev + 1:
            results["issues"].append(f"Heading skip: h{prev} -> h{lvl} ('{clean}')")
            entry["skip"] = True
        results["heading_order"].append(entry)
        prev = lvl

    # 2. Landmark presence
    landmarks = {
        "header": bool(re.search(r'<header[\s>]', html)),
        "nav":      bool(re.search(r'<nav[\s>]', html)),
        "main":     bool(re.search(r'<main[\s>]', html)),
        "aside":    bool(re.search(r'<aside[\s>]', html)),
    }
    results["landmarks"] = landmarks
    for name, present in landmarks.items():
        if not present:
            results["issues"].append(f"Missing landmark: <{name}>")

    # 3. List semantics - divs with list-like class names (skip hidden elements)
    for m in re.finditer(r'<div\b([^>]*)>', html, re.IGNORECASE):
        full_tag = m.group(0)  # entire <div ...> tag
        if 'hidden' in full_tag:
            continue  # hidden elements not in a11y tree
        cls_m = re.search(r'class="([^"]*(?:list|menu)[^"]*)"', full_tag, re.IGNORECASE)
        if cls_m:
            results["lists_ok"] = False
            results["issues"].append(f"Possible list using <div class='{cls_m.group(1)}'> (should be <ul>/<li>)")

    # 4. Table headers
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
    for i, tbl in enumerate(tables):
        if '<th' not in tbl:
            results["tables_ok"] = False
            results["issues"].append(f"Table {i+1} missing <th> header cells")

    return results

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "index.html"
    r = verify_a11y_tree(path)
    print(json.dumps(r, indent=2))
    if r["issues"]:
        print(f"\n{'='*40}\nFAIL: {len(r['issues'])} issue(s)", file=sys.stderr)
        for iss in r["issues"]:
            print(f"  \u2717 {iss}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n\u2713 All ARIA tree checks passed")
