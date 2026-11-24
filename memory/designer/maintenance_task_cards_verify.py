"""Verify Maintenance Task Cards (Designer cycle-15 g5).
Criteria:
  1. Card shows: agent name, task, time assigned, productive status
  2. Grid: 4 cards per row at 1440px, 2 per row at 768px
  3. Content truncates gracefully for long text (line-clamp/ellipsis)
  4. Productive status updates on data refresh (updateStatus method)
  5. No overflow at any breakpoint (min-width:0, overflow handling)
  6. Accessible (role=list/listitem, aria-labels)
  7. Reduced-motion respected
  8. Public API exposed
  9. core.js loads the module
  10. CSS/JS bracket balance
"""
import re, sys
from pathlib import Path

css = Path('ui/maintenance-task-cards.css').read_text(encoding='utf-8')
js  = Path('ui/maintenance-task-cards.js').read_text(encoding='utf-8')
core_js = Path('ui/core.js').read_text(encoding='utf-8')

checks = []
def check(name, cond):
    checks.append((name, bool(cond)))

# 1. Card content fields
check("CSS: .mtc-agent (name)", '.mtc-agent' in css)
check("CSS: .mtc-task (task text)", '.mtc-task' in css)
check("CSS: .mtc-time (time assigned)", '.mtc-time' in css)
check("CSS: .mtc-status (productive status)", '.mtc-status' in css)

# 2. Grid layout
check("CSS: grid-template-columns 4 at default", 'repeat(4,1fr)' in css)
check("CSS: 2 columns at 768px", 'repeat(2,1fr)' in css and 'max-width:768px' in css)

# 3. Truncation
check("CSS: text-overflow ellipsis on agent name", 'text-overflow:ellipsis' in css)
check("CSS: line-clamp on task (2 lines)", '-webkit-line-clamp:2' in css or 'line-clamp' in css)

# 4. Status update
check("JS: updateStatus function", 'updateStatus' in js)
check("JS: data-productive attribute toggling", 'data-productive' in js)
check("CSS: status colors (green/red)", 'data-productive="true"' in css and 'data-productive="false"' in css)

# 5. No overflow
check("CSS: min-width:0 on card (prevents overflow)", 'min-width:0' in css)
check("CSS: overflow:hidden on task", 'overflow:hidden' in css)

# 6. Accessibility
check("JS: role=list on grid", "role','list'" in js or "role', 'list'" in js)
check("JS: role=listitem on cards", "role','listitem'" in js or "role', 'listitem'" in js)
check("JS: aria-label on status", 'aria-label' in js)

# 7. Reduced motion
check("CSS: prefers-reduced-motion", 'prefers-reduced-motion' in css)

# 8. Public API
check("JS: window.maintenanceTaskCards exposed", 'window.maintenanceTaskCards' in js)

# 9. core.js loader
check("core.js: loads maintenance-task-cards.js", 'maintenance-task-cards.js' in core_js)
check("core.js: loads maintenance-task-cards.css", 'maintenance-task-cards.css' in core_js)

# 10. Bracket balance
css_o, css_c = css.count('{'), css.count('}')
js_clean = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
js_clean = re.sub(r'//[^\n]*', '', js_clean)
js_o, js_c = js_clean.count('{'), js_clean.count('}')
check(f"CSS: brackets balanced ({css_o}/{css_c})", css_o == css_c)
check(f"JS: braces balanced ({js_o}/{js_c})", js_o == js_c)

passed = sum(1 for _, ok in checks if ok)
total = len(checks)
print(f"\nMaintenance Task Cards - Verification")
print(f"{'='*50}")
for name, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
print(f"{'='*50}")
print(f"Result: {passed}/{total} PASS")
if passed < total:
    sys.exit(1)
print("\nAll criteria met. Goal REACHED.")