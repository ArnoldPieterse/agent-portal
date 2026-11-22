# Goal 1 (WCAG 2.1 AA Audit) - ARIA label fixes 2026-11-21 (pass 2)
Owner: Designer. Status: **In progress** - icon-only buttons now have aria-label.

## What was done this pass
Identified all dynamically-created and static icon-only buttons lacking accessible names, then fixed:

1. **index.html** `#edClose` - added `aria-label="Close editor"` (was title-only on SVG button)
2. **ui/core.js** settings button (`g`) in agent card - added `g.setAttribute("aria-label","Edit "+a.name)` 
3. **ui/core.js** delete button (`x`) in agent card - added `x.setAttribute("aria-label","Delete "+a.name)`

All other buttons (23 of 26) have visible text content serving as their accessible name per WCAG 4.1.2.

## Verification
- Re-ran `wcag_keyboard_aria_audit.py`: PASS 10/10, 0 issues
- Manual check: all icon-only buttons now have aria-label; remaining "no aria-label" buttons all have visible text

## Pin advanced
- Old: 8c84ce86dcd3 (2026-11-21x)
- New: e4ceb485d744 (2026-11-21x)
- Backup: memory/designer/index_html_CANONICAL_e4ceb485d744_2026-11-21x.html

## Remaining for full goal closure
- [x] Color contrast >= 4.5:1 (verified earlier - ALL PASS)
- [x] Keyboard navigation (skip-link + focus-visible + no traps = automated PASS)
- [x] ARIA labels on all icon-only buttons (3 fixed this pass; remaining have visible text)
- [ ] Manual keyboard-only walkthrough in browser (Tab through all panels, verify order)

## Evidence artifacts
- index.html (aria-label on #edClose)
- ui/core.js (aria-label on g and x buttons)
- memory_mirror.py (pin advanced)
