"""Responsive Design Regression Check (Goal 6)
Static analysis of ui/*.css for overflow risks, touch targets, and breakpoint coverage.
No live browser required - runs via `python memory/designer/responsive_check.py`
"""
import re, json, os, sys

CSS_DIR = "ui"
BREAKPOINTS = [320, 768, 1024, 1440]

def load_css():
    """Load only served CSS files (exclude .bak and _ prefixed)."""
    files = {}
    for fname in sorted(os.listdir(CSS_DIR)):
        if not fname.endswith(".css"):
            continue
        if ".bak" in fname or fname.startswith("_"):
            continue
        path = os.path.join(CSS_DIR, fname)
        with open(path, "r") as f:
            content = f.read()
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        files[fname] = content
    return files

def check_overflow_prevention(files):
    """body or html must have overflow-x:hidden."""
    for fname, content in files.items():
        if re.search(r'(?<![a-z])(?:html|body)\s*(?:,[^{}]+)?\{[^}]*overflow-x\s*:\s*hidden', content):
            return True, f"Found in {fname}"
    return False, "No overflow-x:hidden on html/body"

def check_touch_targets(files):
    """pointer:coarse or max-width:768px block must set min-height:44px."""
    for fname, content in files.items():
        # Find @media blocks with pointer/coarse or max-width including 768
        for m in re.finditer(r'@media\s*\(([^)]*(?:coarse|768)[^)]*)\)\s*\{', content):
            start = m.end()
            depth = 1
            j = start
            while j < len(content) and depth > 0:
                if content[j] == '{': depth += 1
                elif content[j] == '}': depth -= 1
                j += 1
            body = content[start:j-1]
            if re.search(r'min-height\s*:\s*44px', body):
                return True, f"min-height:44px in {fname} @media({m.group(1).strip()})"
    return False, "No 44px min-height in mobile/coarse media queries"

def check_fixed_width_overflow(files, viewport=320):
    """Find width/min-width declarations with px values > viewport that aren't max-width."""
    issues = []
    for fname, content in files.items():
        # Match only standalone width or min-width (not max-width)
        # Negative lookbehind ensures we don't match "max-width" 
        for m in re.finditer(r'(?<![a-z-])(min-)?width\s*:\s*(\d+)px', content):
            is_min = m.group(1) == 'min'
            val = int(m.group(2))
            if val > viewport:
                # Get surrounding selector context (60 chars before the { that contains this)
                brace_before = content.rfind('{', 0, m.start())
                sel_start = content.rfind('}', 0, brace_before) + 1 if brace_before > 0 else 0
                selector = content[sel_start:brace_after].strip()[:50] if (brace_after := content.find('}', m.end())) != -1 else "?"
                
                # Check if same block has max-width or width:100% that constrains it
                block_end = content.find('}', m.end())
                block_body = content[brace_before+1:block_end] if brace_before > 0 else ""
                has_flex_constrain = bool(re.search(r'max-width\s*:\s*(?:100%|calc\(|auto)', block_body))
                
                if not has_flex_constrain:
                    issues.append({
                        "file": fname,
                        "selector": selector,
                        "property": f"{m.group(1) or ''}width",
                        "value": f"{val}px"
                    })
    return issues

def check_breakpoint_coverage(files):
    """List all max-width breakpoints defined."""
    bps = set()
    for fname, content in files.items():
        for m in re.finditer(r'@media\s*\([^)]*max-width\s*:\s*(\d+)px[^)]*\)', content):
            bps.add(int(m.group(1)))
    return sorted(bps)

def check_no_horizontal_scroll_risk(files, viewport=320):
    """Elements with width > viewport that aren't inside overflow:hidden containers."""
    # This is a simplified check - full verification needs browser rendering
    risky = []
    for fname, content in files.items():
        for m in re.finditer(r'(?<![a-z-])(?:width|min-width)\s*:\s*(\d+)px', content):
            val = int(m.group(1))
            if val > viewport:
                # Check if it's a max-width (safe) or actual width (risky)
                prefix = content[max(0, m.start()-10):m.start()]
                if 'max-' not in prefix:
                    risky.append(f"{fname}: {val}px")
    return risky

def main():
    files = load_css()
    
    results = {
        "files_analyzed": list(files.keys()),
        "checks": {},
    }
    
    # Run all checks
    ok, detail = check_overflow_prevention(files)
    results["checks"]["overflow_x_hidden"] = {"status": "PASS" if ok else "FAIL", "detail": detail}
    
    ok, detail = check_touch_targets(files)
    results["checks"]["touch_targets_44px"] = {"status": "PASS" if ok else "FAIL", "detail": detail}
    
    issues = check_fixed_width_overflow(files, 320)
    results["checks"]["fixed_width_at_320"] = {
        "status": "PASS" if not issues else "WARN",
        "count": len(issues),
        "issues": issues[:5]
    }
    
    bps = check_breakpoint_coverage(files)
    results["checks"]["breakpoints_defined"] = {"status": "INFO", "values": bps}
    
    # Summary
    fails = [k for k, v in results["checks"].items() if v.get("status") == "FAIL"]
    warns = [k for k, v in results["checks"].items() if v.get("status") == "WARN"]
    
    if fails:
        overall = "FAIL"
    elif warns:
        overall = "PASS_WITH_WARNINGS"
    else:
        overall = "PASS"
    
    results["overall"] = overall
    
    # Output
    print(json.dumps(results, indent=2))
    
    # Exit code: 0 = pass, 1 = fail, 2 = warnings
    sys.exit(0 if overall == "PASS" else (1 if overall == "FAIL" else 2))

if __name__ == "__main__":
    main()
