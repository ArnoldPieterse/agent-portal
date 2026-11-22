#!/usr/bin/env python3
"""
WCAG 2.1 AA Audit - Keyboard Navigation + ARIA Labels (Goal 1)
Usage: python memory/designer/wcag_keyboard_aria_audit.py
"""
import re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def read(p):
    full = os.path.join(ROOT, p)
    if not os.path.exists(full):
        return ""
    with open(full) as f:
        return f.read()

html  = read("index.html")
css   = read("ui/app.css")
core  = read("ui/core.js")
comps = read("ui/components.js") if os.path.exists(os.path.join(ROOT, "ui/components.js")) else ""

issues = []
passes = []

# --- 1. Skip-to-content link ---
if re.search(r'skip.*?content|skip-to', html, re.I):
    passes.append("Skip-to-content link present in index.html")
else:
    issues.append("MISSING: skip-to-content link in index.html")

# --- 2. Focus-visible / :focus coverage ---
has_global_focus_visible = bool(re.search(r':focus-visible', css))
if has_global_focus_visible:
    passes.append("Global :focus-visible rule(s) present in app.css")

# Check for outline:none without alternative visible indicator
focus_rules = re.findall(r'([^{}]+):focus(?:-visible)?\s*\{([^}]+)\}', css)
no_outline_no_alt = []
for selector, body in focus_rules:
    sel_clean = selector.strip().split(',')[0].strip()
    if ('outline:none' in body or 'outline: none' in body):
        if 'border-color' not in body and 'box-shadow' not in body:
            no_outline_no_alt.append(sel_clean)

if no_outline_no_alt:
    issues.append("FOCUS REMOVED without visible alternative on: " + str(no_outline_no_alt))
else:
    passes.append("All :focus rules with outline:none have border-color or box-shadow alternative")

# --- 3. ARIA labels on buttons ---
buttons_html = re.findall(r'<button[^>]*>', html)
buttons_js = re.findall(r'<button[^>]*>', core + comps)
all_buttons = buttons_html + buttons_js
missing_aria = []
for btn in all_buttons:
    if 'aria-label' not in btn and 'title=' not in btn:
        missing_aria.append(btn.strip()[:80])

if missing_aria:
    passes.append("Buttons found: %d; %d lack explicit aria-label (may have visible text - manual check needed)"
                  % (len(all_buttons), len(missing_aria)))
else:
    passes.append("All buttons have aria-label or title attribute")

# --- 4. Keyboard trap check ---
tabindex_neg = re.findall(r'tabindex=-1[^>]*>', html + core)
if tabindex_neg:
    issues.append("Potential keyboard traps: %d elements with tabindex=-1" % len(tabindex_neg))
else:
    passes.append("No tabindex=-1 elements detected (no obvious keyboard traps)")

# --- 5. Landmarks ---
for lm in ['<nav', '<main', '<aside']:
    if lm in html:
        passes.append("Landmark present: " + lm.strip('<'))
    else:
        issues.append("MISSING landmark: " + lm.strip('<'))

# --- 6. Heading order ---
headings = re.findall(r'<h([1-6])', html)
prev_level = 0
heading_issues = []
for i, h in enumerate(headings):
    level = int(h)
    if prev_level > 0 and level > prev_level + 1:
        heading_issues.append("h%d after h%d (position %d)" % (level, prev_level, i))
    prev_level = level

if heading_issues:
    issues.extend(heading_issues)
else:
    passes.append("Heading order correct (%d headings, no skips)" % len(headings))

# --- 7. Touch targets ---
small_targets = []
for selector, body in re.findall(r'([^{}]+)\{([^}]+)\}', css):
    if any(kw in selector.lower() for kw in ['button', 'input', '.seg ', '#modeBar']):
        h_match = re.search(r'(?:min-)?height:\s*(\d+)px', body)
        if h_match and int(h_match.group(1)) < 44:
            small_targets.append(selector.strip()[:50])

if small_targets:
    issues.append("Potential touch targets <44px: " + str(small_targets[:5]))
else:
    passes.append("No obviously undersized interactive elements in CSS")

# --- Report ---
print("=" * 60)
print("WCAG 2.1 AA - Keyboard Nav + ARIA Audit (Goal 1)")
print("Files audited: index.html, ui/app.css, ui/core.js, ui/components.js")
print("=" * 60)
print()
print("PASSED CHECKS (%d):" % len(passes))
for p in passes:
    print("  [PASS] " + p)
print()
print("ISSUES FOUND (%d):" % len(issues))
if issues:
    for i in issues:
        print("  [FAIL] " + i)
else:
    print("  (none)")
print()

critical = [i for i in issues if 'MISSING' in i or 'FOCUS REMOVED' in i or 'keyboard trap' in i.lower()]
if critical:
    print("VERDICT: FAIL - %d critical issue(s)" % len(critical))
else:
    print("VERDICT: PASS (%d minor note(s))" % len(issues))

print()
print("Manual follow-ups:")
print("  - Tab through all panels in browser, verify logical order")
print("  - Verify .ft-host focus (outline:none + stroke change) is visible enough")
print("  - Check icon-only buttons have text alternative or aria-label")

sys.exit(1 if critical else 0)
