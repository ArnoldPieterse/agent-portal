"""visual_regression.py - DOM-level structural regression for portal panels.

Since no headless browser is available in the sandbox, this performs
DOM-structural fingerprinting instead of pixel-diff:
  1. Parses index.html + ui/*.css
  2. Extracts visible-element tree at each breakpoint (1920/768/375)
     by evaluating CSS media queries against element display/visibility
  3. Produces a JSON fingerprint (element list with class, tag, parent path)
  4. Compares fingerprints: flags panels where >2% of elements changed

Usage:
  python memory/verifier/visual_regression.py --baseline   # save baseline
  python memory/verifier/visual_regression.py              # compare vs baseline
  python memory/verifier/visual_regression.py --test       # self-test with intentional change
"""
import json, sys, os, re, hashlib
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # project root
INDEX_HTML = ROOT / "index.html"
UI_DIR = ROOT / "ui"
BASELINE_FILE = Path(__file__).parent / "visual_baseline.json"
BREAKPOINTS = [1920, 768, 375]
THRESHOLD = 0.02  # 2%

class DOMFingerprint(HTMLParser):
    """Extract visible elements at a given viewport width."""
    
    def __init__(self, media_rules):
        super().__init__()
        self.media_rules = media_rules  # dict: (selector, prop, value) -> min_width/max_width
        self.elements = []
        self.stack = []
        self.current_attrs = {}
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        path = "/".join(self.stack) + "/" + tag
        self.elements.append({
            "tag": tag,
            "path": path,
            "id": attrs_dict.get("id", ""),
            "class": attrs_dict.get("class", ""),
        })
        # Don't push void elements
        if tag not in ("br", "hr", "img", "input", "meta", "link"):
            self.stack.append(tag)
            
    def handle_endtag(self, tag):
        if tag in self.stack:
            # Pop to matching tag (handle implicit closing)
            while self.stack and self.stack[-1] != tag:
                self.stack.pop()
            if self.stack:
                self.stack.pop()

def parse_css_media_rules(css_text):
    """Extract media query rules as (selector, property, value, min_width, max_width)."""
    rules = []
    # Find @media blocks
    for m in re.finditer(r'@media[^{]*\((?:min|max)-width:\s*(\d+)px\)[^{]*\{', css_text):
        block_start = m.end()
        min_w = max_w = None
        if 'min-width' in m.group(0):
            min_w = int(re.search(r'(\d+)px', m.group(0)).group(1))
        if 'max-width' in m.group(0):
            max_w = int(re.search(r'(\d+)px', m.group(0)).group(1))
        
        # Extract rules within this block (simplified - count braces)
        depth = 1
        i = block_start
        while i < len(css_text) and depth > 0:
            if css_text[i] == '{': depth += 1
            elif css_text[i] == '}': depth -= 1
            i += 1
        block = css_text[block_start:i-1]
        
        # Extract simple rules from block
        for rm in re.finditer(r'([^{}]+)\{([^{}]+)\}', block):
            selector = rm.group(1).strip()
            props = rm.group(2).strip()
            for pm in re.finditer(r'(\w[\w-]*)\s*:\s*([^;]+);?', props):
                rules.append({
                    "selector": selector,
                    "prop": pm.group(1),
                    "value": pm.group(2).strip(),
                    "min_width": min_w,
                    "max_width": max_w,
                })
    return rules

def is_visible_at(rule, width):
    """Check if a media rule applies at given viewport width."""
    if rule["min_width"] is not None and width < rule["min_width"]:
        return False
    if rule["max_width"] is not None and width > rule["max_width"]:
        return False
    return True

def apply_media_rules(elements, rules, width):
    """Filter/annotate elements based on media query visibility."""
    # Build a set of selectors that are display:none at this width
    hidden_selectors = set()
    for r in rules:
        if is_visible_at(r, width) and r["prop"] == "display" and r["value"] == "none":
            hidden_selectors.add(r["selector"])
    
    visible = []
    for el in elements:
        # Check if element matches any hidden selector (simplified: id or class match)
        hidden = False
        for sel in hidden_selectors:
            sel_clean = sel.strip()
            if sel_clean.startswith("#") and el["id"] == sel_clean[1:]:
                hidden = True; break
            elif sel_clean.startswith(".") and el["class"] and sel_clean[1:] in el["class"].split():
                hidden = True; break
        if not hidden:
            visible.append(el)
    return visible

def fingerprint_html(html_text, css_text, width):
    """Produce a structural fingerprint at given viewport width."""
    parser = DOMFingerprint(None)
    parser.feed(html_text)
    all_elements = parser.elements
    
    rules = parse_css_media_rules(css_text)
    visible = apply_media_rules(all_elements, rules, width)
    
    # Sort for stable comparison
    visible.sort(key=lambda e: (e["path"], e["tag"], e["id"], e["class"]))
    return visible

def load_portal_files():
    """Load index.html and all ui/*.css."""
    html_text = INDEX_HTML.read_text(encoding="utf-8") if INDEX_HTML.exists() else "<html><body></body></html>"
    css_parts = []
    for f in sorted(UI_DIR.glob("*.css")):
        css_parts.append(f.read_text(encoding="utf-8"))
    return html_text, "\n".join(css_parts)

def generate_baseline():
    """Generate and save baseline fingerprint."""
    html_text, css_text = load_portal_files()
    baseline = {}
    for bp in BREAKPOINTS:
        elements = fingerprint_html(html_text, css_text, bp)
        baseline[str(bp)] = {
            "count": len(elements),
            "elements": elements,
            "hash": hashlib.sha256(json.dumps(elements, sort_keys=True).encode()).hexdigest()[:16],
        }
    BASELINE_FILE.write_text(json.dumps(baseline, indent=2))
    print(f"[BASELINE] Saved to {BASELINE_FILE.name}")
    for bp in BREAKPOINTS:
        print(f"  {bp}px: {baseline[str(bp)]['count']} elements (hash={baseline[str(bp)]['hash']})")

def compare():
    """Compare current state against baseline. Exit 1 if >2% change."""
    if not BASELINE_FILE.exists():
        print("[ERROR] No baseline found. Run with --baseline first.")
        sys.exit(1)
    
    baseline = json.loads(BASELINE_FILE.read_text())
    html_text, css_text = load_portal_files()
    
    total_changes = 0
    total_elements = 0
    panels_flagged = []
    
    for bp in BREAKPOINTS:
        key = str(bp)
        current = fingerprint_html(html_text, css_text, bp)
        current.sort(key=lambda e: (e["path"], e["tag"], e["id"], e["class"]))
        
        base_elems = baseline[key]["elements"]
        curr_set = set(json.dumps(e, sort_keys=True) for e in current)
        base_set = set(json.dumps(e, sort_keys=True) for e in base_elems)
        
        added = curr_set - base_set
        removed = base_set - curr_set
        changed = len(added) + len(removed)
        total = max(len(base_set), len(curr_set), 1)
        pct = changed / total
        
        total_changes += changed
        total_elements += total
        
        status = "OK" if pct <= THRESHOLD else "FLAGGED"
        print(f"  {bp}px: {len(base_elems)} base vs {len(current)} current | {changed} diff ({pct:.1%}) [{status}]")
        
        if pct > THRESHOLD:
            panels_flagged.append({"breakpoint": bp, "added": len(added), "removed": len(removed), "pct": round(pct, 4)})
    
    overall_pct = total_changes / max(total_elements, 1)
    print(f"\n[RESULT] Overall: {total_changes}/{total_elements} elements changed ({overall_pct:.2%})")
    
    if panels_flagged:
        print(f"[FAIL] {len(panels_flagged)} breakpoint(s) exceed {THRESHOLD:.0%} threshold:")
        for p in panels_flagged:
            print(f"  {p['breakpoint']}px: +{p['added']} -{p['removed']} ({p['pct']:.1%})")
        sys.exit(1)
    else:
        print("[PASS] All breakpoints within threshold.")
        sys.exit(0)

def self_test():
    """Self-test: create a test HTML, baseline it, modify it, confirm flag."""
    import tempfile, shutil
    
    test_dir = Path(tempfile.mkdtemp())
    test_html = test_dir / "index.html"
    test_ui = test_dir / "ui"
    test_ui.mkdir()
    
    # Original
    original_html = """<html><head><link rel="stylesheet" href="ui/app.css"></head>
<body>
<div id="panel-fleet"><h2>Fleet</h2><p>Status: OK</p></div>
<div id="panel-goals"><h2>Goals</h2><p>80 total</p></div>
<div id="panel-ops"><h2>Ops</h2><p>All clear</p></div>
</body></html>"""
    test_html.write_text(original_html)
    (test_ui / "app.css").write_text("#panel-ops { display: none; } @media (max-width: 768px) { #panel-goals { display: none; } }")
    
    # Monkey-patch paths for test
    global INDEX_HTML, UI_DIR, BASELINE_FILE
    orig_index, orig_ui, orig_base = INDEX_HTML, UI_DIR, BASELINE_FILE
    INDEX_HTML, UI_DIR, BASELINE_FILE = test_html, test_ui, test_dir / "baseline.json"
    
    try:
        # Step 1: Baseline
        print("[TEST] Generating baseline...")
        generate_baseline()
        
        # Step 2: Compare (should pass)
        print("\n[TEST] Comparing unchanged (expect PASS)...")
        import subprocess
        result = subprocess.run([sys.executable, __file__], capture_output=True, text=True, cwd=str(Path(__file__).parent))
        # Can't easily re-run in same process with patched paths, so do inline:
        baseline_data = json.loads(BASELINE_FILE.read_text())
        html_text, css_text = load_portal_files()
        for bp in BREAKPOINTS:
            current = fingerprint_html(html_text, css_text, bp)
            base_elems = baseline_data[str(bp)]["elements"]
            curr_set = set(json.dumps(e, sort_keys=True) for e in current)
            base_set = set(json.dumps(e, sort_keys=True) for e in base_elems)
            changed = len(curr_set - base_set) + len(base_set - curr_set)
            total = max(len(base_set), 1)
            assert changed / total <= THRESHOLD, f"Unchanged should pass at {bp}px"
        print("  PASS: unchanged state matches baseline")
        
        # Step 3: Intentional change (add a panel + remove one)
        print("\n[TEST] Applying intentional UI change...")
        modified_html = """<html><head><link rel="stylesheet" href="ui/app.css"></head>
<body>
<div id="panel-fleet"><h2>Fleet</h2><p>Status: OK</p></div>
<div id="panel-goals"><h2>Goals</h2><p>80 total</p></div>
<div id="panel-NEW"><h2>New Panel</h2><p>Added</p></div>
</body></html>"""  # Removed panel-ops, added panel-NEW
        test_html.write_text(modified_html)
        
        # Step 4: Compare (should fail)
        print("[TEST] Comparing modified (expect FAIL/FLAGGED)...")
        baseline_data = json.loads(BASELINE_FILE.read_text())
        html_text, css_text = load_portal_files()
        flagged = False
        for bp in BREAKPOINTS:
            current = fingerprint_html(html_text, css_text, bp)
            base_elems = baseline_data[str(bp)]["elements"]
            curr_set = set(json.dumps(e, sort_keys=True) for e in current)
            base_set = set(json.dumps(e, sort_keys=True) for e in base_elems)
            changed = len(curr_set - base_set) + len(base_set - curr_set)
            total = max(len(base_set), 1)
            pct = changed / total
            print(f"  {bp}px: {changed}/{total} changed ({pct:.1%})")
            if pct > THRESHOLD:
                flagged = True
        assert flagged, "Intentional change should be flagged!"
        print("  PASS: intentional change correctly flagged")
        
        print("\n[SELF-TEST COMPLETE] All assertions passed.")
    finally:
        INDEX_HTML, UI_DIR, BASELINE_FILE = orig_index, orig_ui, orig_base
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    if "--baseline" in sys.argv:
        generate_baseline()
    elif "--test" in sys.argv:
        self_test()
    else:
        compare()
