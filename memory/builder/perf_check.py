#!/usr/bin/env python3
"""Portal Performance Budget check - Builder c5#10
Measures: total JS size (gzipped), CSS size, HTML size.
Thresholds: total JS < 200KB gzipped, initial load resources < 500KB total.
Run: python memory/builder/perf_check.py
"""
import gzip, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PASS, FAIL = 0, 0

def check(desc, ok, detail=""):
    global PASS, FAIL
    status = "\u2713" if ok else "\u2717"
    print(f"  {status} {desc}" + (f" [{detail}]" if detail else ""))
    if ok: PASS += 1
    else: FAIL += 1

print("=== Portal Performance Budget (c5#10) ===\n")

# Collect all JS files served by /ui/ route
js_files = []
for root, dirs, files in os.walk(os.path.join(BASE, "ui")):
    for f in files:
        if f.endswith(".js"):
            js_files.append(os.path.join(root, f))

total_js_raw = 0
total_js_gz = 0
print("  JS files:")
for jf in sorted(js_files):
    with open(jf, "rb") as f:
        raw = f.read()
    gz = gzip.compress(raw, compresslevel=9)
    total_js_raw += len(raw)
    total_js_gz += len(gz)
    rel = os.path.relpath(jf, BASE)
    print(f"    {rel}: {len(raw)/1024:.1f}KB raw / {len(gz)/1024:.1f}KB gz")

# CSS files
css_files = []
for root, dirs, files in os.walk(os.path.join(BASE, "ui")):
    for f in files:
        if f.endswith(".css"):
            css_files.append(os.path.join(root, f))

total_css_raw = 0
total_css_gz = 0
print("\n  CSS files:")
for cf in sorted(css_files):
    with open(cf, "rb") as f:
        raw = f.read()
    gz = gzip.compress(raw, compresslevel=9)
    total_css_raw += len(raw)
    total_css_gz += len(gz)
    rel = os.path.relpath(cf, BASE)
    print(f"    {rel}: {len(raw)/1024:.1f}KB raw / {len(gz)/1024:.1f}KB gz")

# HTML
with open(os.path.join(BASE, "index.html"), "rb") as f:
    html_raw = f.read()
html_gz = gzip.compress(html_raw, compresslevel=9)

print(f"\n  index.html: {len(html_raw)/1024:.1f}KB raw / {len(html_gz)/1024:.1f}KB gz")

# Budget checks
print("\n  --- Budget Checks ---")
JS_BUDGET = 200 * 1024  # 200KB
TOTAL_BUDGET = 500 * 1024  # 500KB total initial load (HTML+CSS+JS gzipped)

total_gz = total_js_gz + total_css_gz + len(html_gz)

check(f"Total JS < 200KB gzipped: {total_js_gz/1024:.1f}KB",
      total_js_gz < JS_BUDGET, f"{total_js_gz/1024:.1f}/{200}KB")
check(f"Total initial load (HTML+CSS+JS) < 500KB gzipped: {total_gz/1024:.1f}KB",
      total_gz < TOTAL_BUDGET, f"{total_gz/1024:.1f}/500KB")

# CLS proxy: check for images without dimensions (common CLS cause)
with open(os.path.join(BASE, "index.html"), "r", encoding="utf-8") as f:
    html = f.read()
import re
imgs = re.findall(r"<img[^>]*>", html)
no_dims = [i[:60] for i in imgs if "width" not in i and "height" not in i and "style" not in i]
check(f"No images missing dimensions (CLS risk): {len(no_dims)} found",
      len(no_dims) == 0, str(no_dims[:2]))

print(f"\n=== Result: {PASS} pass, {FAIL} fail ===")
sys.exit(1 if FAIL > 0 else 0)
