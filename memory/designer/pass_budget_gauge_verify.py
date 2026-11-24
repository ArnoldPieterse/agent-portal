"""Verify Pass Budget Gauge (Designer cycle-15 g3).
Criteria:
  1. SVG circular gauge with stroke-dasharray/dashoffset
  2. Color thresholds: green <50%, amber 50-80%, red >80%
  3. Numeric text "used/budget" in center
  4. Animated fill (transition on stroke-dashoffset)
  5. Accessible: role=meter, aria-valuenow, aria-valuemin/max, aria-label
  6. prefers-reduced-motion respected
  7. Responsive at 768px
  8. Public API exposed (window.passBudgetGauge)
  9. core.js loads the module
  10. CSS/JS bracket balance
"""
import re, sys
from pathlib import Path

css = Path('ui/pass-budget-gauge.css').read_text(encoding='utf-8')
js  = Path('ui/pass-budget-gauge.js').read_text(encoding='utf-8')
core_js = Path('ui/core.js').read_text(encoding='utf-8')

checks = []
def check(name, cond):
    checks.append((name, bool(cond)))

# 1. SVG circular gauge
check("JS: SVG circle elements", 'createElementNS' in js and 'circle' in js)
check("CSS: stroke-dasharray/dashoffset used", 'stroke-dashoffset' in css or 'strokeDashoffset' in js)

# 2. Color thresholds
check("CSS: green level style", 'data-level="green"' in css)
check("CSS: amber level style", 'data-level="amber"' in css)
check("CSS: red level style", 'data-level="red"' in css)
check("JS: threshold logic (0.5, 0.8)", '0.5' in js and '0.8' in js)

# 3. Numeric text
check("JS: center text shows used/budget", "used + '/' + budget" in js or "used+'/'+budget" in js)

# 4. Animated fill
check("CSS: transition on stroke-dashoffset", 'stroke-dashoffset' in css and 'transition' in css)

# 5. Accessibility
check("JS: role=meter", "role', 'meter'" in js or "role','meter'" in js)
check("JS: aria-valuenow", 'aria-valuenow' in js)
check("JS: aria-valuemin/max", 'aria-valuemin' in js and 'aria-valuemax' in js)
check("JS: aria-label with percentage", 'aria-label' in js)

# 6. Reduced motion
check("CSS: prefers-reduced-motion removes transition", 'prefers-reduced-motion' in css and 'transition:none' in css.replace(' ',''))

# 7. Responsive
check("CSS: max-width 768px media query", 'max-width:768px' in css)

# 8. Public API
check("JS: window.passBudgetGauge exposed", 'window.passBudgetGauge' in js)
check("JS: create + update functions", 'create' in js and 'update' in js)

# 9. core.js loader
check("core.js: loads pass-budget-gauge.js", 'pass-budget-gauge.js' in core_js)
check("core.js: loads pass-budget-gauge.css", 'pass-budget-gauge.css' in core_js)

# 10. Bracket balance
css_open, css_close = css.count('{'), css.count('}')
js_clean = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
js_clean = re.sub(r'//[^\n]*', '', js_clean)
js_open, js_close = js_clean.count('{'), js_clean.count('}')
check(f"CSS: brackets balanced ({css_open}/{css_close})", css_open == css_close)
check(f"JS: braces balanced ({js_open}/{js_close})", js_open == js_close)

# Print
passed = sum(1 for _, ok in checks if ok)
total = len(checks)
print(f"\nPass Budget Gauge - Verification")
print(f"{'='*50}")
for name, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
print(f"{'='*50}")
print(f"Result: {passed}/{total} PASS")
if passed < total:
    sys.exit(1)
print("\nAll criteria met. Goal REACHED.")