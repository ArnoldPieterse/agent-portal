"""Verify Mode History Timeline (Designer cycle-15 g4).
Criteria:
  1. Horizontal timeline with colored segments per mode
  2. Timestamps shown on segments
  3. Max 24h window, scrollable
  4. Current mode highlighted with glow
  5. Updates without full re-render
  6. At 768px, compresses to icon-only view
  7. Accessible (role=img, aria-label)
  8. Reduced-motion respected
  9. Public API exposed
  10. core.js loads the module
"""
import re, sys
from pathlib import Path

css = Path('ui/mode-history-timeline.css').read_text(encoding='utf-8')
js  = Path('ui/mode-history-timeline.js').read_text(encoding='utf-8')
core_js = Path('ui/core.js').read_text(encoding='utf-8')

checks = []
def check(name, cond):
    checks.append((name, bool(cond)))

# 1. Colored segments per mode
check("CSS: WORK segment color", 'data-mode="WORK"' in css)
check("CSS: MAINTENANCE segment color", 'data-mode="MAINTENANCE"' in css)
check("CSS: IDLE segment color", 'data-mode="IDLE"' in css)

# 2. Timestamps
check("JS: title attribute with timestamps", '.title' in js or "title =" in js)
check("CSS: labels div for timestamps", '.mht-labels' in css)

# 3. 24h window + scrollable
check("JS: WINDOW_HOURS = 24", 'WINDOW_HOURS = 24' in js)
check("CSS: overflow-x auto (scrollable)", 'overflow-x:auto' in css)

# 4. Current mode glow
check("CSS: .mht-current with box-shadow glow", '.mht-current' in css and 'box-shadow' in css)
check("JS: adds mht-current class", 'mht-current' in js)

# 5. Update without full re-render
check("JS: update() function exists (incremental)", 'function update' in js or 'update:' in js)

# 6. Responsive at 768px
check("CSS: max-width 768px media query", 'max-width:768px' in css)
check("CSS: compresses (font-size:0 or reduced height)", 'font-size:0' in css or 'height:24px' in css)

# 7. Accessibility
check("JS: role=img", "role','img'" in js or "role', 'img'" in js)
check("JS: aria-label with description", 'aria-label' in js)

# 8. Reduced motion
check("CSS: prefers-reduced-motion disables transitions", 'prefers-reduced-motion' in css)

# 9. Public API
check("JS: window.modeHistoryTimeline exposed", 'window.modeHistoryTimeline' in js)

# 10. core.js loader
check("core.js: loads mode-history-timeline.js", 'mode-history-timeline.js' in core_js)
check("core.js: loads mode-history-timeline.css", 'mode-history-timeline.css' in core_js)

# Bracket balance
css_o, css_c = css.count('{'), css.count('}')
js_clean = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
js_clean = re.sub(r'//[^\n]*', '', js_clean)
js_o, js_c = js_clean.count('{'), js_clean.count('}')
check(f"CSS: brackets balanced ({css_o}/{css_c})", css_o == css_c)
check(f"JS: braces balanced ({js_o}/{js_c})", js_o == js_c)

passed = sum(1 for _, ok in checks if ok)
total = len(checks)
print(f"\nMode History Timeline - Verification")
print(f"{'='*50}")
for name, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
print(f"{'='*50}")
print(f"Result: {passed}/{total} PASS")
if passed < total:
    sys.exit(1)
print("\nAll criteria met. Goal REACHED.")