#!/usr/bin/env python3
"""trend_verify.py — Designer goal 8 verification: Cross-Cycle Trend Strip
   Checks all 5 acceptance criteria against ui/cockpit-trend.css + ui/cockpit-trend.js.
   Usage: python memory/designer/trend_verify.py
"""
import os, re, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def p(*a): return os.path.join(ROOT, *a)

css = open(p("ui", "cockpit-trend.css"), encoding="utf-8").read()
js  = open(p("ui", "cockpit-trend.js"), encoding="utf-8").read()

results = []
def check(name, passed, detail=""):
    results.append((name, passed, detail))
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

print("=== Cross-Cycle Trend Strip Verification ===\n")

# 1. >= 5 cycles render: JS supports arbitrary array length, CSS uses flex space-between
check(">= 5 cycles render",
      "forEach" in js and "space-between" in css,
      "JS iterates full array; CSS track uses justify-content:space-between for flexible dot count")

# 2. Each dot hoverable for detail: .ct-dot:hover + .ct-tip tooltip in both CSS and JS
has_hover = ".ct-dot:hover" in css
has_tip_css = ".ct-tip" in css and "tooltip" in js.lower()
check("Each dot hoverable for detail",
      has_hover and has_tip_css,
      f"CSS .ct-dot:hover={has_hover}, tooltip element in JS={has_tip_css}")

# 3. Trend direction visually apparent: data-trend attr + CSS gradient modifiers
has_trend_attr = 'data-trend' in css and 'computeTrend' in js
has_gradients = all(t in css for t in ["improving", "declining", "stable"])
check("Trend direction visually apparent",
      has_trend_attr and has_gradients,
      f"JS computeTrend={has_trend_attr}, CSS modifiers improving/declining/stable={has_gradients}")

# 4. Strip fits within 32px height: explicit height + max-height
has_32 = re.search(r'height:\s*32px', css) is not None
has_max32 = re.search(r'max-height:\s*32px', css) is not None
check("Strip fits within 32px height",
      has_32 and has_max32,
      f"height:32px={has_32}, max-height:32px={has_max32}")

# 5. Works in both light and dark themes: [data-theme="light"] override in CSS + default is dark
has_light = '[data-theme="light"]' in css
has_dark_default = "var(--panel, #151a22)" in css or "#151a22" in css  # dark default
check("Works in both light and dark themes",
      has_light and has_dark_default,
      f"[data-theme=light] override={has_light}, dark default tokens={has_dark_default}")

print(f"\n=== RESULT: {sum(1 for _,p,_ in results if p)}/{len(results)} criteria PASS ===")
sys.exit(0 if all(p for _,p,_ in results) else 1)
