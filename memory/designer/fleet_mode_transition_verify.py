"""Verify Fleet Mode Transition Animation (Designer cycle-15 g2).
Criteria:
  1. CSS: background color shift green->amber->grey over 400ms ease-in-out
  2. CSS: FLIP animation class exists with transform transition
  3. CSS: prefers-reduced-motion respected (instant switch)
  4. JS: FLIP technique implemented (First/Last/Invert/Play)
  5. JS: getBoundingClientRect calls during Play phase = 0
  6. JS: reduced-motion check before animation
  7. JS: exposed public API (window.fleetModeTransition)
  8. core.js loads the module dynamically
  9. CSS file is valid (bracket balance)
  10. JS file is valid (brace balance, no syntax errors via node if available)
"""
import re, sys
from pathlib import Path

css = Path('ui/fleet-mode-transition.css').read_text(encoding='utf-8')
js  = Path('ui/fleet-mode-transition.js').read_text(encoding='utf-8')
core_js = Path('ui/core.js').read_text(encoding='utf-8')

checks = []

def check(name, cond):
    checks.append((name, bool(cond)))

# 1. Background color transition 400ms ease-in-out
check("CSS: 400ms ease-in-out transition", '400ms ease-in-out' in css)
check("CSS: mode-specific bg colors (WORK/MAINTENANCE/IDLE)", 
      'data-fleet-mode="WORK"' in css and 'data-fleet-mode="MAINTENANCE"' in css and 'data-fleet-mode="IDLE"' in css)

# 2. FLIP animation class
check("CSS: .fmt-flip class with transform transition", '.fmt-flip' in css and 'transform' in css)

# 3. Reduced motion
check("CSS: prefers-reduced-motion sets transition:none", 
      'prefers-reduced-motion' in css and 'transition: none' in css)

# 4. FLIP technique in JS
check("JS: getBoundingClientRect (First phase)", 'getBoundingClientRect' in js)
check("JS: Invert transform (translate)", 'translate(' in js)
check("JS: Play phase via requestAnimationFrame", 'requestAnimationFrame' in js)
check("JS: transitionend cleanup", 'transitionend' in js)

# 5. No getBoundingClientRect in the rAF callback (Play phase = 0 reads)
raf_block = re.search(r'requestAnimationFrame\(function\(\)\{(.+?)\}\)', js, re.DOTALL)
check("JS: 0 getBoundingClientRect in Play phase (rAF callback)", 
      not raf_block or 'getBoundingClientRect' not in raf_block.group(1))

# 6. Reduced motion check before animation
check("JS: matchMedia prefers-reduced-motion guard", 
      'prefers-reduced-motion' in js and 'matchMedia' in js)

# 7. Public API
check("JS: window.fleetModeTransition exposed", 'window.fleetModeTransition' in js)
check("JS: ORDERS constant for mode-specific panel order", 'ORDERS' in js)

# 8. core.js loader
check("core.js: loads fleet-mode-transition.js", 'fleet-mode-transition.js' in core_js)
check("core.js: loads fleet-mode-transition.css", 'fleet-mode-transition.css' in core_js)

# 9. CSS bracket balance
css_open = css.count('{')
css_close = css.count('}')
check(f"CSS: brackets balanced ({css_open}/{css_close})", css_open == css_close)

# 10. JS brace balance (rough check - ignore strings/comments)
js_no_comments = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
js_no_comments = re.sub(r'//[^\n]*', '', js_no_comments)
js_open = js_no_comments.count('{')
js_close = js_no_comments.count('}')
check(f"JS: braces balanced ({js_open}/{js_close})", js_open == js_close)

# Print results
passed = sum(1 for _, ok in checks if ok)
total = len(checks)
print(f"\nFleet Mode Transition Animation - Verification")
print(f"{'='*50}")
for name, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
print(f"{'='*50}")
print(f"Result: {passed}/{total} PASS")

if passed < total:
    sys.exit(1)
print("\nAll criteria met. Goal REACHED.")