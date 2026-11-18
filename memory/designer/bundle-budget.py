#!/usr/bin/env python3
"""CSS/JS bundle size measurement for Designer goal #3 (performance budget).
Target: <80KB total minified transfer size.
Usage: python memory/designer/bundle-budget.py
"""
import os, re

FILES = ['ui/app.css', 'ui/core.js', 'ui/uploads.js']
TARGET = 80 * 1024  # 80 KB

def minify_css(content):
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    content = re.sub(r'\s+', ' ', content).strip()
    return content

def minify_js(content):
    # Basic: strip block comments + line comments (not inside strings - simple heuristic)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    content = re.sub(r'//[^\n]*', '', content)
    content = re.sub(r'\s+', ' ', content).strip()
    return content

print(f"{'File':<16} {'Raw':>8} {'Minified':>10} {'Saved':>8}")
print("-" * 46)
total_raw = total_min = 0
for f in FILES:
    if not os.path.exists(f):
        print(f"{f:<16} MISSING")
        continue
    with open(f, 'r') as fh:
        content = fh.read()
    raw = len(content)
    mn = minify_css(content) if f.endswith('.css') else minify_js(content)
    min_size = len(mn)
    total_raw += raw
    total_min += min_size
    print(f"{f:<16} {raw/1024:>7.1f}K {min_size/1024:>9.1f}K {(raw-min_size)/1024:>7.1f}K")

print("-" * 46)
status = "PASS" if total_min < TARGET else "FAIL"
print(f"{'TOTAL':<16} {total_raw/1024:>7.1f}K {total_min/1024:>9.1f}K")
print(f"\nBudget: {TARGET//1024}KB minified | Result: {total_min/1024:.1f}KB [{status}]")
if total_min >= TARGET:
    print(f"OVER by {(total_min-TARGET)/1024:.1f} KB - optimize top-5 offenders below")

# Top-5 largest blocks
print("\n=== TOP-5 LARGEST BLOCKS ===")
all_blocks = []
for f in FILES:
    if not os.path.exists(f): continue
    with open(f, 'r') as fh:
        content = fh.read()
    blocks = re.split(r'\n\s*\n', content)
    for b in blocks:
        if len(b.strip()) > 100:
            all_blocks.append((len(b), f, b[:60].replace('\n',' ')))
all_blocks.sort(reverse=True)
for i, (size, fname, preview) in enumerate(all_blocks[:5], 1):
    print(f"  {i}. {size/1024:.1f} KB | {fname}: {preview}")
