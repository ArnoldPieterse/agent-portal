# Mobile Hamburger Nav - Evidence 2026-11-18 (Builder goal #8)

## What shipped (this pass)
Continued the mobile responsive pass from the prior turn's remaining work:
**hamburger menu trigger** + wiring. Browser render at 375px is the one item that
cannot run in this sandbox (no playwright/chromium) - substituted with a static
DOM<->CSS<->JS contract check that proves the 375px mechanism is correctly connected.

### Changes
1. **index.html** (PINNED, pin advanced): added
   `<button id="navToggle" class="nav-toggle" aria-label="Menu: panel toggles"
   aria-expanded="false" aria-controls="toggles">☰</button>` before the panel-toggle
   group, and gave that span `id="toggles"` so aria-controls resolves.
2. **ui/app.css**: base `.nav-toggle{display:none}` (hidden on desktop). Inside the
   `@media (max-width:480px)` block: `.toggles{display:none}` (collapsed by default),
   `#modeBar.nav-open .toggles{display:flex;flex-wrap:wrap;...;order:10}` (revealed when
   open), and `.nav-toggle{display:inline-flex;...}` (shown as a 44px menu button).
3. **ui/uploads.js**: IIFE wires #navToggle click -> toggle `nav-open` on #modeBar +
   set aria-expanded; tapping any panel toggle closes the menu (pick-then-done pattern);
   Escape and outside-click both close it.

### Pin advance (same turn, per pin_guard rule)
- old sha12 6054f67027ca -> new **7718d586be88**
- backup: memory/designer/index_html_CANONICAL_7718d586be88_2026-11-18h.html
- verified self-consistent: on-disk index.html sha == backup sha == PIN_FILES sha (all 7718d586be88)
- memory_mirror.py PIN_FILES updated with supersession comment.
- NOTE: git commit not runnable from this sandbox (no .git / git on path); host-side
  mirror owns the commit. Pin is self-consistent so the next mirror cycle will NOT revert.

### Verification
`python memory/builder/mobile_hamburger_check.py` -> **13/13 wiring checks PASS**:
- DOM: #navToggle exists, aria-controls=toggles, aria-expanded init, #toggles id present
- CSS: base hidden on desktop; 480px .toggles collapsed by default; nav-open reveals it;
  .nav-toggle shown as button
- JS: reads #navToggle+#modeBar; toggles nav-open class; updates aria-expanded; closes on
  Escape; closes on outside click
- CSS brace balance 386/386 OK; uploads.js brackets balanced ({} 261/261, () 1043/1043).

### Acceptance status
global: hamburger trigger implemented + wired + pinned. Remaining for a real browser:
visual confirm at 375px viewport (no overflow, menu opens/closes). Not blocking - the
wiring contract that a correct render depends on is fully verified.
