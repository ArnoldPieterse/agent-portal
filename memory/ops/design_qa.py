#!/usr/bin/env python3
"""
design_qa.py - Static design QA for the portal UI.
Run: python memory/ops/design_qa.py
Checks:
  1. CSS custom-property integrity: every var(--x) used has a :root definition
  2. Theme parity: all themes define the same set of custom properties
  3. Icon registry: every icon requested in JS exists in icons.js
  4. Dead file detection: files in ui/ not referenced by index.html or @import chains
"""
import re, os, sys, json

UI = "ui"

# --- 1. CSS var integrity ---
def collect_css_vars(css_dir=UI):
    """Return (defined, used) sets across all loaded CSS files."""
    defined = set()
    used = set()
    # Gather all CSS content (loaded + @imported)
    css_files = []
    for f in os.listdir(css_dir):
        if f.endswith(".css"):
            css_files.append(os.path.join(css_dir, f))
    content = ""
    for cf in css_files:
        try:
            with open(cf, encoding="utf-8") as fh:
                content += fh.read()
        except: pass
    defined.update(re.findall(r'(?:^|[\s{;])(--[^\s:;{}]+)\s*:', content))
    used.update(re.findall(r'var\(\s*(--[\w-]+)', content))
    return defined, used

# --- 2. Theme parity ---
def theme_parity(css_dir=UI):
    """Check that [data-theme=x] blocks override the same COLOR vars as :root.
    Spacing/radius/type tokens are shared (defined once in :root) - only color
    tokens need per-theme overrides."""
    issues = []
    try:
        with open(os.path.join(css_dir, "tokens.css"), encoding="utf-8") as f:
            tokens = f.read()
    except: return issues
    # Only check color-like tokens (those whose values look like colors)
    COLOR_RE = re.compile(r'^(#[0-9a-fA-F]{3,8}|rgba?\(|hsl)')
    root_color_vars = set()
    for m in re.finditer(r'(--[^\s:;{}]+)\s*:\s*([^;}{]+)', tokens):
        if COLOR_RE.match(m.group(2).strip()):
            root_color_vars.add(m.group(1))
    # Extract [data-theme=x] blocks
    for theme_m in re.finditer(r'\[data-theme=([a-z]+)\]\{([^}]+)\}', tokens):
        theme_name = theme_m.group(1)
        body = theme_m.group(2)
        theme_color_vars = set()
        for m in re.finditer(r'(--[^\s:;{}]+)\s*:\s*([^;}{]+)', body):
            if COLOR_RE.match(m.group(2).strip()):
                theme_color_vars.add(m.group(1))
        missing = root_color_vars - theme_color_vars
        # Some vars are intentionally shared (spacing, radius, type)
        if missing:
            issues.append(f"Theme '{theme_name}' missing {len(missing)} color overrides (sample: {sorted(list(missing))[:5]})")
    return issues

# --- 3. Icon registry check ---
def icon_check():
    """Verify every icon name requested in JS exists in icons.js."""
    issues = []
    try:
        with open(os.path.join(UI, "icons.js"), encoding="utf-8") as f:
            icon_src = f.read()
    except: return ["icons.js not found"]
    # Icons are defined as unquoted keys: `agent: '<svg...>`
    defined_icons = set(re.findall(r'^\s{4}(\w+)\s*:', icon_src, re.MULTILINE))
    # Scan all loaded JS for UI.icon('name') / UI.iconSized('name', px) calls
    js_files = [f for f in os.listdir(UI) if f.endswith(".js") and f != "icons.js"]
    requested = set()
    for jf in js_files:
        try:
            with open(os.path.join(UI, jf), encoding="utf-8") as f:
                src = f.read()
            # Strip comments to avoid matching usage docs
            src = re.sub(r'/\*.*?\*/', '', src, flags=re.DOTALL)
            src = re.sub(r'//.*', '', src)
            requested.update(re.findall(r'UI\.icon(?:Sized)?\(\s*["\']([a-z0-9_-]+)["\']', src))
        except: pass
    missing = requested - defined_icons
    if missing:
        issues.append(f"Icons requested but not in registry: {sorted(missing)}")
    return issues

# --- 4. Dead file detection ---
def dead_files():
    """Find ui/ files not referenced by index.html or @import/script chains."""
    try:
        with open("index.html", encoding="utf-8") as f:
            html = f.read()
    except: return []
    # Collect all ui/ references in HTML (relative: src="ui/x.js" or href="ui/x.css")
    refs = set(re.findall(r'["\']ui/([\w.-]+)["\']', html))
    # Add @import chain from loaded CSS files
    for cssf in [f for f in os.listdir(UI) if f.endswith(".css") and f in refs]:
        try:
            with open(os.path.join(UI, cssf), encoding="utf-8") as f:
                content = f.read()
            imports = re.findall(r'@import\s+["\']([^"\']+)["\']', content)
            for imp in imports:
                refs.add(imp.replace("./", "").lstrip("/ui/"))
        except: pass
    dead = []
    for f in os.listdir(UI):
        if f.startswith("_") or f.endswith(".bak") or ".bak-" in f: continue
        if f not in refs:
            dead.append(f)
    return sorted(dead)

# --- Main ---
def main():
    print("=" * 60)
    print("DESIGN QA REPORT")
    print("=" * 60)
    ok = True

    # Check 1
    defined, used = collect_css_vars()
    # Vars set dynamically via JS inline styles (not in any CSS file)
    DYNAMIC_VARS = {'--gauge-target', '--ring-circumference', '--ring-offset', '--stagger-i'}
    undefined_used = (used - defined) - DYNAMIC_VARS
    if undefined_used:
        ok = False
        print(f"\n[FAIL] CSS vars used but never defined ({len(undefined_used)}):")
        for v in sorted(undefined_used):
            print(f"  {v}")
    else:
        print(f"\n[PASS] CSS var integrity: {len(used)} vars used, all defined.")

    # Check 2
    parity_issues = theme_parity()
    if parity_issues:
        ok = False
        print(f"\n[WARN] Theme parity issues:")
        for i in parity_issues:
            print(f"  {i}")
    else:
        print("[PASS] Theme parity: all themes define consistent var sets.")

    # Check 3
    icon_issues = icon_check()
    if icon_issues:
        ok = False
        print(f"\n[FAIL] Icon registry issues:")
        for i in icon_issues:
            print(f"  {i}")
    else:
        print("[PASS] Icon registry: all requested icons exist.")

    # Check 4
    dead = dead_files()
    if dead:
        print(f"\n[INFO] Unreferenced ui/ files ({len(dead)}): {dead}")
    else:
        print("[PASS] No dead ui/ files detected.")

    print("\n" + "=" * 60)
    print(f"RESULT: {'PASS' if ok else 'ISSUES FOUND'}")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()