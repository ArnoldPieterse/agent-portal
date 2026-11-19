# Designer Goal #8 — Icon System: refresh/reset glyphs -> SVG (progress, 2026-11-19)

## What changed this pass
- **ui/icons.js**: added `refresh` (Feather rotate-cw) + `reset` (rotate-ccw), both 24x24 / 1.5px stroke / currentColor. Icon count 22 -> **24**. All 24 entries verified well-formed (<svg ... /> with valid child elements; 'play' uses <polygon>).
- **index.html** (markup-only, no script added): replaced the 3 rendered icon-glyphs in buttons with inline 1.5px-stroke SVG matching the existing pattern (cf. Ops wrench button L36):
  - #resetBtn: U+21BA (↺) -> reset SVG + "Reset"
  - #actRefresh: U+21BB (↻) -> refresh SVG + "refresh"
  - #filesRefresh: U+21BB (↻) -> refresh SVG + "refresh"

## Pin advanced SAME turn (pin_guard rule)
- new index.html sha12 = **441391c8492d** (was d51c43756597 pre-edit; old pin 815d64fa70b5)
- backup: memory/designer/index_html_CANONICAL_441391c8492d_2026-11-19x.html
- PIN_FILES (memory_mirror.py L240-241) updated to 441391c8492d; verified live=pin=backup all match.
- Prior work preserved: ui/icons.js + ui/tour.js + ui/fleet_topology.js script tags all still present in new canonical.

## Measured state (non-browser, static)
- Rendered refresh/reset icon-glyphs in index.html: **0** (was 3).
- Remaining non-ASCII in UI files are LEGITIMATE TYPOGRAPHY / inline log text, NOT icons:
  ellipsis …(U+2026), em/en-dash —/–(U+2014/U+2013), bullet •(U+2022) in prose; arrows inside
  status strings (core.js "item(s) -> TODO_completed.md", "agent<->agent counter"); U+2713/U+2717
  check/cross in uploads.js state labels. Two U+21BB remain ONLY in code comments (uploads.js L326, app.css L147).

## NOT yet closed (do not overclaim)
- Verifier's open concern on "used consistently across panels": UI.icon() JS call-sites exist in core.js
  (actIcons, emptyState, goalBar save) + uploads.js; index.html now uses inline SVG (same style) rather than
  JS injection because it is markup-only. Full "no emoji remain" + render check still needs a browser session
  (NEEDS-HUMAN logged in memory/ops/blockers.md). Ledger stays OPEN pending browser acceptance.

## git
- `git` not on PATH at this seat (shutil.which('git')=None); commit could not run here. Files + pin advanced
  in the shared agent folder are the durable artifacts; a seat with git can `git add index.html ui/icons.js memory_mirror.py && git commit`.
