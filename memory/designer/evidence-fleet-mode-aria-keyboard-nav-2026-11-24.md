# Fleet Mode ARIA + Keyboard Nav - Evidence (2026-11-24)

## What was done
1. **ARIA live region** (`ui/fleet-mode-aria.js`): `role="status"`, `aria-live="polite"`, `aria-atomic="true"` div injected into DOM. Announces "Fleet entered [mode] mode" on every actual transition (not initial load). Auto-clears after 3s to prevent re-announcement spam.

2. **Keyboard navigation** (`ui/fleet-mode-aria.js`): ArrowLeft/ArrowRight cycles focus between all 5 cockpit panel toggles (goalsBtn, actBtn, fleetBtn, filesBtn, opsBtn) in a ring. Escape closes any open panel. Fleet badge (tabindex=0) opens cockpit on Enter.

3. **Focus-visible styles** (`ui/fleet-mode-aria.css`): `:focus-visible` outline + box-shadow on `.toggles button` and `.seg button` in all three mode states. No mode state removes the focus indicator.

4. **Visible badge**: Fixed top-right pill showing current mode with color-coded dot (green/amber/grey). Pulse animation respects `prefers-reduced-motion`.

5. **Wiring**: CSS already imported via `@import "fleet-mode-aria.css"` in `ui/app.css`. JS added as `<script src="ui/fleet-mode-aria.js">` in index.html after cockpit.js (pin advanced: sha12 87a60ffb0b8c).

## Verification
- All 5 PANEL_IDS confirmed present in index.html DOM.
- CSS @import chain: app.css → fleet-mode-aria.css ✓
- JS loaded after cockpit.js (dependency order correct) ✓
- No dependencies beyond native DOM API + fetch ✓
- Reduced-motion media query disables all animations ✓

## Files touched
- `index.html` — added script tag (pin advanced to 87a60ffb0b8c)
- `memory_mirror.py` — PIN_FILES updated
- `memory/designer/index_html_CANONICAL_87a60ffb0b8c_2026-11-24x.html` — new canonical backup

## Status: REACHED
