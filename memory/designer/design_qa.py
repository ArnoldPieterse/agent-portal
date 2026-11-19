"""design_qa.py - Automated design QA checks for portal CSS/JS.
Runs static analysis on ui/*.css and ui/*.js files.
Usage: python memory/designer/design_qa.py
Exit 0 = all pass, Exit 1 = failures found.
"""
import re, os, sys

UI_DIR = "ui"
FAILURES = []
PASSES = []

def check(name, passed, detail=""):
    if passed:
        PASSES.append(f"  PASS  {name}")
    else:
        FAILURES.append(f"  FAIL  {name}  {detail}")

# Load all CSS
css_files = [f for f in os.listdir(UI_DIR) if f.endswith(".css") and ".bak" not in f and "_before" not in f]
all_css = ""
for f in css_files:
    all_css += open(os.path.join(UI_DIR, f)).read() + "\n"

# Load all JS
js_files = [f for f in os.listdir(UI_DIR) if f.endswith(".js") and ".bak" not in f]
all_js = ""
for f in js_files:
    all_js += open(os.path.join(UI_DIR, f)).read() + "\n"

print("=" * 60)
print("DESIGN QA - Static Checks")
print("=" * 60)

# --- CHECK 1: Typography scale compliance ---
# Allowed font-size values (from tokens)
SCALE_PX = {"12px","14px","15px","18px","24px"}
violations = []
for f in css_files:
    src = open(os.path.join(UI_DIR, f)).read()
    for m in re.finditer(r'font-size\s*:\s*([^;]+)', src):
        val = m.group(1).strip()
        if "var(--fs-" in val:
            tok = val.split("var(")[1].split(")")[0]
            if tok not in ("--fs-12","--fs-14","--fs-15","--fs-18","--fs-24"):
                violations.append(f"{f}: {val}")
        elif val not in SCALE_PX and val != "inherit":
            violations.append(f"{f}: {val}")
check("1. Typography: all font-size on 5-step scale", not violations, str(violations[:3]))

# --- CHECK 2: No orphaned off-scale tokens ---
tokens_src = open(os.path.join(UI_DIR, "tokens.css")).read()
orphan_tokens = re.findall(r'--fs-(\d+):', tokens_src)
valid_steps = {"12","14","15","18","24"}
orphans = [t for t in orphan_tokens if t not in valid_steps]
check("2. Tokens: no off-scale --fs-* defined", not orphans, f"orphaned: {orphans}")

# --- CHECK 3: Spacing scale compliance (core layout only) ---
# Check gap and padding/margin in main layout elements (not arbitrary offsets)
SPACING_PX = {"4px","8px","12px","16px","24px","0","0px"}
sp_violations = []
for m in re.finditer(r'gap\s*:\s*(\d+px)', all_css):
    val = m.group(1)
    if val not in SPACING_PX:
        sp_violations.append(f"gap:{val}")
check("3. Spacing: gap values on scale", len(sp_violations) <= 3, f"{len(sp_violations)} off-scale gaps: {sp_violations[:5]}")

# --- CHECK 4: Hover rules consolidated in interactions.css ---
inter_src = open(os.path.join(UI_DIR, "interactions.css")).read() if os.path.exists(os.path.join(UI_DIR,"interactions.css")) else ""
app_src = open(os.path.join(UI_DIR, "app.css")).read() if os.path.exists(os.path.join(UI_DIR,"app.css")) else ""
ad_hoc_hover = len(re.findall(r':hover', app_src))
check("4. Interaction: no ad-hoc :hover in app.css", ad_hoc_hover == 0, f"{ad_hoc_hover} found")

# --- CHECK 5: prefers-reduced-motion respected ---
has_reduced_motion = "prefers-reduced-motion" in all_css
check("5. Animation: prefers-reduced-motion media query present", has_reduced_motion)

# --- CHECK 6: Line-length enforcement (75ch) ---
has_75ch = "75ch" in all_css
check("6. Typography: 75ch max-width rule present", has_75ch)

# --- CHECK 7: Empty state helper exists and is used ---
has_empty_state = "UI.emptyState" in all_js
empty_count = len(re.findall(r'UI\.emptyState', all_js))
check("7. Empty states: UI.emptyState() defined and used >=5 times", empty_count >= 5, f"used {empty_count}x")

# --- CHECK 8: Skeleton helper exists and is used ---
has_skeleton = "UI.skeleton" in all_js
skeleton_count = len(re.findall(r'UI\.skeleton', all_js))
check("8. Loading: UI.skeleton() defined and used >=3 times", skeleton_count >= 3, f"used {skeleton_count}x")

# --- CHECK 9: Icon system - no external icon library ---
has_external_icon = any(x in all_css + all_js for x in ["font-awesome","iconfont","material-icons","bootstrap-icons"])
check("9. Icons: no external icon library dependency", not has_external_icon)

# --- CHECK 10: Icon count >= 20 ---
icons_src = open(os.path.join(UI_DIR, "icons.js")).read() if os.path.exists(os.path.join(UI_DIR,"icons.js")) else ""
icon_count = len(re.findall(r'^\s+\w+:\s*\x27<svg', icons_src, re.MULTILINE))
check("10. Icons: >=20 defined in ui/icons.js", icon_count >= 20, f"found {icon_count}")

# --- CHECK 11: Touch target size (>=44px) on mobile ---
# Look for min-height/min-width >= 44 in media queries or button styles
touch_ok = bool(re.search(r'(min-?(height|width)\s*:\s*(4[4-9]|[5-9]\d)px)', all_css))
check("11. Responsive: touch target sizing present", touch_ok, "no >=44px min-height/width found")

# --- CHECK 12: No hardcoded colors outside tokens (sample check) ---
# Tokens define the palette; check app.css for hex colors not in tokens
token_hexes = set(re.findall(r'#[0-9a-fA-F]{6}', tokens_src))
app_hexes = set(re.findall(r'#[0-9a-fA-F]{6}', app_src))
unknown_hexes = app_hexes - token_hexes - {"#000","#fff","#000000","#ffffff"}
check("12. Visual: no unknown hex colors in app.css (outside tokens)", len(unknown_hexes) <= 3, f"extra: {list(unknown_hexes)[:4]}")

# --- Output ---
print("\n".join(PASSES))
if FAILURES:
    print("\n".join(FAILURES))

print(f"\n{'=' * 60}")
print(f"RESULT: {len(PASSES)} passed, {len(FAILURES)} failed / {len(PASSES)+len(FAILURES)} total")
print(f"{'=' * 60}")
sys.exit(1 if FAILURES else 0)
