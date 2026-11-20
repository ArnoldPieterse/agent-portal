<!-- PROVENANCE agent=designer goal=6 date=2026-11-20 -->
# Goal 6 - Responsive Hardening: Pass 1 (static overflow + touch targets)

## What was done
Static analysis of ui/app.css identified 5 fixed-width elements that would cause horizontal scroll at ≤375px:
- `.chipfile` width:360px → `max-width:calc(100vw - 24px)`
- `#actSel` width:360px → `max-width:calc(100vw - 24px)`
- `#fleetTopo` width:860px → `width:100%;overflow-x:auto`
- `.toast-container` width:320px → `calc(100vw - 16px)`
- `#peek` width:340px → already covered by existing `max-width:calc(100vw - 24px)` at 768px

Touch targets: added `min-height:44px` to `.seg button`, `#send`, `.panel-toggle`, `.toggles button`, `.acard` in the ≤375px block.
New 320px breakpoint: tighter padding, reduced aside height, smaller seg buttons.

## Remaining (needs CDP or live browser)
- Verify no overflow at exactly 320px/768px/1024px/1440px via screenshots
- Confirm touch targets render ≥44px in practice
- Check fleet topology panel reflow at 768px (it's a wide SVG/canvas)

**Status: in progress** - static fixes applied; live verification pending.
