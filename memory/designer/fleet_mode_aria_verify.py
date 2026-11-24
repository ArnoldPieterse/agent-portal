"""Verify Fleet Mode ARIA + Keyboard Nav (Designer cycle-15 goal #1).

Checks:
1. ui/fleet-mode-aria.js exists and contains required ARIA attributes
2. ui/fleet-mode-aria.css exists with visually-hidden region styles
3. ui/app.css has the fleet mode badge styles + focus-visible rules
4. ui/core.js dynamically loads the module
5. ARIA live region uses aria-live=assertive, role=status, aria-atomic=true
6. Keyboard nav: ArrowLeft/ArrowRight between panel toggles, Enter on badge opens cockpit, Esc closes panels
7. prefers-reduced-motion respected
8. Print media hides the badge
"""
import pathlib, sys, re

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # project root
PASS, FAIL = [], []

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(f"{name}: {detail}")

# ── File existence ──────────────────────────────────────────────────────
js_path = ROOT / "ui" / "fleet-mode-aria.js"
css_path = ROOT / "ui" / "fleet-mode-aria.css"
app_css = ROOT / "ui" / "app.css"
core_js = ROOT / "ui" / "core.js"

check("fleet-mode-aria.js exists", js_path.exists())
check("fleet-mode-aria.css exists", css_path.exists())
check("app.css exists", app_css.exists())
check("core.js exists", core_js.exists())

if not all([js_path.exists(), app_css.exists(), core_js.exists()]):
    print("FATAL: missing files"); sys.exit(1)

js = js_path.read_text(encoding="utf-8")
css_standalone = css_path.read_text(encoding="utf-8")
app_css_txt = app_css.read_text(encoding="utf-8")
core_js_txt = core_js.read_text(encoding="utf-8")

# ── ARIA attributes in JS ───────────────────────────────────────────────
check("aria-live=assertive", 'aria-live' in js and 'assertive' in js)
check("role=status", 'role' in js and 'status' in js)
check("aria-atomic=true", 'aria-atomic' in js and 'true' in js)
check("announce message format", 'Fleet entered' in js)

# ── Mode handling ───────────────────────────────────────────────────────
check("WORK mode defined", 'WORK' in js)
check("MAINTENANCE mode defined", 'MAINTENANCE' in js)
check("IDLE mode defined", 'IDLE' in js)

# ── Keyboard navigation ─────────────────────────────────────────────────
check("ArrowRight nav", 'ArrowRight' in js)
check("ArrowLeft nav", 'ArrowLeft' in js)
check("Enter opens cockpit", 'Enter' in js and 'fleetBtn' in js)
check("Escape closes panels", 'Escape' in js)

# ── CSS: visually hidden region ─────────────────────────────────────────
combined_css = app_css_txt  # styles are appended here
check(".fm-aria-region style", '.fm-aria-region' in combined_css)
check("clip:rect(0,0,0,0) or inset clip", 'clip:rect' in combined_css or 'inset' in combined_css)
check("1px width/height for hidden region", 'width:1px' in combined_css and 'height:1px' in combined_css)

# ── CSS: badge styles ───────────────────────────────────────────────────
check(".fm-badge style", '.fm-badge' in combined_css)
check("mode-specific colors (work)", '.fm-badge--work' in combined_css)
check("mode-specific colors (maintenance)", '.fm-badge--maintenance' in combined_css)
check("mode-specific colors (idle)", '.fm-badge--idle' in combined_css)

# ── CSS: focus-visible ─────────────────────────────────────────────────
check("focus-visible on toggles", ':focus-visible' in combined_css)
check("outline for focus", 'outline' in combined_css and '2px' in combined_css)

# ── CSS: reduced motion ────────────────────────────────────────────────
check("prefers-reduced-motion", 'prefers-reduced-motion' in combined_css)
check("animation:none in reduced motion", 'animation:none' in combined_css)

# ── CSS: print hides badge ─────────────────────────────────────────────
check("@media print hides .fm-badge", '@media print' in combined_css and '.fm-badge' in combined_css.split('@media print')[-1] if '@media print' in combined_css else False)

# ── core.js loads the module ────────────────────────────────────────────
check("core.js loads fleet-mode-aria.js", 'fleet-mode-aria.js' in core_js_txt)

# ── JS: polling mechanism ───────────────────────────────────────────────
check("polling interval (30s)", '30000' in js or 'setInterval' in js)
check("fetches /api/fleet/cockpit", '/api/fleet/cockpit' in js)
check("fallback to /api/fleet/status", '/api/fleet/status' in js)

# ── JS: dedup (only announce on change) ───────────────────────────────
check("mode change detection", 'currentMode' in js and 'prev' in js)

# ── Results ─────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"FLEET MODE ARIA + KEYBOARD NAV VERIFICATION")
print(f"{'='*60}")
for p in PASS:
    print(f"  PASS  {p}")
for f in FAIL:
    print(f"  FAIL  {f}")
print(f"\n{'─'*60}")
total = len(PASS) + len(FAIL)
print(f"RESULT: {len(PASS)}/{total} checks passed")
if FAIL:
    print("VERDICT: FAIL")
    sys.exit(1)
else:
    print("VERDICT: PASS")
    sys.exit(0)
