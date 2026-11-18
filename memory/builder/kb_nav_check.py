#!/usr/bin/env python3
"""Keyboard Navigation audit - Builder c5#9
Checks: focus rings, ARIA labels, tab order, keyboard handlers.
Run: python memory/builder/kb_nav_check.py
"""
import re, sys, os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PASS, FAIL, WARN = 0, 0, 0

def check(desc, ok, detail=""):
    global PASS, FAIL, WARN
    if ok:
        PASS += 1
        print(f"  \u2713 {desc}")
    else:
        FAIL += 1
        print(f"  \u2717 {desc}" + (f" [{detail}]" if detail else ""))

print("=== Keyboard Navigation Audit (c5#9) ===\n")

# 1. Focus ring CSS - global :focus-visible rule
with open(os.path.join(BASE, "ui/app.css"), "r", encoding="utf-8") as f:
    css = f.read()

check("Global :focus-visible rule present (button/input/select/textarea/a/[tabindex])",
      re.search(r"button:focus-visible.*?input:focus-visible.*?\[tabindex\]:focus-visible", css, re.S) is not None)

# 2. ARIA labels on interactive elements in index.html
with open(os.path.join(BASE, "index.html"), "r", encoding="utf-8") as f:
    html = f.read()

buttons = re.findall(r"<button[^>]*>(.*?)</button>", html, re.S)
aria_count = len(re.findall(r"aria-label=", html))
print(f"  Info: {len(buttons)} buttons found, {aria_count} aria-label attributes total")

# Check icon-only buttons (text <= 2 chars or just an emoji/symbol) have aria-label
icon_buttons_missing = []
for m in re.finditer(r"<button([^>]*)>(.*?)</button>", html, re.S):
    attrs, content = m.group(1), m.group(2).strip()
    # Strip HTML entities and check if text is just icon/symbol
    text_only = re.sub(r"[\s\u4e00-\u9fff]", "", content)
    is_icon_only = len(content) <= 2 or all(ord(c) > 127 for c in content if c not in " ")
    if is_icon_only and "aria-label" not in attrs:
        btn_id = re.search(r'id="([^"]+)"', attrs)
        icon_buttons_missing.append(btn_id.group(1) if btn_id else content[:20])

check(f"All icon-only buttons have aria-label ({len(icon_buttons_missing)} missing)",
      len(icon_buttons_missing) == 0, str(icon_buttons_missing))

# 3. role="tablist" on mode selector
check("Chat mode nav has role='tablist'", 'role="tablist"' in html)
check("Mode buttons have role='tab' + aria-selected", 
      html.count('role="tab"') >= 2 and 'aria-selected=' in html)

# 4. Keyboard event handlers in JS
js_files = ["ui/core.js", "ui/uploads.js"]
all_js = ""
for jf in js_files:
    try:
        with open(os.path.join(BASE, jf), "r", encoding="utf-8") as f:
            all_js += f.read()
    except: pass

check("Escape key handler present (closes panels/nav)", 
      re.search(r"key.*===?.*Escape|Escape.*key", all_js) is not None)
check("Enter key handler present (activates focused elements)",
      re.search(r"key.*===?.*Enter|Enter.*key", all_js) is not None)

# 5. tabindex on dynamic elements (timeline nodes)
check("Dynamic interactive elements have tabindex=0",
      'tabindex="0"' in html or "tabindex" in all_js)

# 6. aria-live for status updates
check("aria-live region for status messages", 
      'aria-live="polite"' in html)

# 7. No tabindex > 0 (breaks natural tab order)
tabindex_positive = re.findall(r'tabindex="([1-9])"', html)
check("No positive tabindex values (preserves DOM order)", len(tabindex_positive) == 0, str(tabindex_positive))

print(f"\n=== Result: {PASS} pass, {FAIL} fail, {WARN} warn ===")
sys.exit(1 if FAIL > 0 else 0)
