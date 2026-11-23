#!/usr/bin/env python3
"""
cockpit_a11y_gate.py - Verifier Goal #9 (Cycle 14)
Cockpit A11y Gate (WCAG AA): automated contrast, keyboard-nav, ARIA-label check
on all cockpit panels.

Checks:
  1. CONTRAST: foreground/background color pairs in CSS meet WCAG AA ratios
     (normal text >= 4.5:1, large text >= 3:1)
  2. KEYBOARD-NAV: interactive elements (buttons, links, inputs) have visible
     focus styles (:focus or :focus-visible rules present in CSS)
  3. ARIA-LABELS: cockpit panel headings and interactive controls have appropriate
     ARIA roles/labels or text content

Acceptance criteria:
  * All 3 check categories run against index.html + ui/app.css + ui/tokens.css
  * Contrast violations reported with element selector + computed ratio + required ratio
  * Keyboard focus styles detected (at least one :focus rule exists)
  * ARIA/label coverage reported per panel type
  * Self-test proves both pass and fail branches for each category

Usage:
  python memory/verifier/cockpit_a11y_gate.py --self-test
  python memory/verifier/cockpit_a11y_gate.py
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
INDEX_HTML = BASE / "index.html"
CSS_FILES = [BASE / "ui" / f for f in ["app.css", "tokens.css"] if (BASE / "ui" / f).exists()]
RESULTS_FILE = BASE / "memory" / "verifier" / "cockpit_a11y_gate_results.jsonl"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Color utilities for contrast calculation
# ---------------------------------------------------------------------------

def hex_to_rgb(hex_color):
    """Convert hex color (#RGB or #RRGGBB) to (r,g,b) tuple 0-255."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c*2 for c in hex_color)
    if len(hex_color) != 6:
        return None
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def relative_luminance(rgb):
    """Compute WCAG relative luminance from (r,g,b)."""
    def srgb_to_linear(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = [srgb_to_linear(c) for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color1, color2):
    """Compute WCAG contrast ratio between two hex colors."""
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    if not rgb1 or not rgb2:
        return None
    l1 = relative_luminance(rgb1)
    l2 = relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------------------
# Check 1: CONTRAST
# ---------------------------------------------------------------------------

def check_contrast(css_content, html_content):
    """Extract color pairs from CSS and verify WCAG AA contrast."""
    # Extract color tokens from :root variables
    root_colors = {}
    for m in re.finditer(r'--(\w+):\s*(#[0-9a-fA-F]{3,8})', css_content):
        root_colors[m.group(1)] = m.group(2)
    
    # Find common fg/bg pairs: text-color on background
    # Look for explicit color/background declarations in selectors that apply to panels
    violations = []
    passed_pairs = []
    
    # Find all CSS rules (selector { body }) and check for color+background pairs
    rule_pattern = re.compile(r'([^{}]+)\{([^}]+)\}', re.DOTALL)
    color_re = re.compile(r'(?:^|;)\s*color:\s*(#[0-9a-fA-F]{3,8})')
    bg_re = re.compile(r'background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,8})')
    
    for m in rule_pattern.finditer(css_content):
        selector = m.group(1).strip()[:60]
        body = m.group(2)
        cm = color_re.search(body)
        bm = bg_re.search(body)
        if not cm or not bm:
            continue
        fg = cm.group(1)
        bg = bm.group(1)
        
        ratio = contrast_ratio(fg, bg)
        if ratio is None:
            continue
        
        # Determine if this is likely large text (heading) or normal text
        is_large = bool(re.search(r'(h[1-6]|\.title|\.header)', selector))
        required = 3.0 if is_large else 4.5
        
        entry = {"selector": selector, "fg": fg, "bg": bg, "ratio": round(ratio, 2), "required": required}
        if ratio < required:
            violations.append(entry)
        else:
            passed_pairs.append(entry)
    
    return {
        "check": "contrast",
        "pairs_checked": len(violations) + len(passed_pairs),
        "violations": violations,
        "passed": len(passed_pairs),
        "pass": len(violations) == 0,
    }


# ---------------------------------------------------------------------------
# Check 2: KEYBOARD NAVIGATION (focus styles)
# ---------------------------------------------------------------------------

def check_keyboard_nav(css_content, html_content):
    """Check that focus styles exist for interactive elements."""
    # Look for :focus or :focus-visible rules
    focus_rules = re.findall(r'([^{}]*:focus(?:-visible)?[^{}]*)\{([^}]+)\}', css_content)
    
    # Check what properties the focus rules set (outline, box-shadow, border, etc.)
    visible_focus_props = ['outline', 'box-shadow', 'border', 'background', 'color']
    has_visible_focus = False
    for selector, body in focus_rules:
        if any(prop in body for prop in visible_focus_props):
            # Make sure it's not outline: none or visibility: hidden
            if 'outline: none' not in body and 'outline:none' not in body.replace(' ', ''):
                has_visible_focus = True
                break
    
    # Count interactive elements in HTML
    buttons = len(re.findall(r'<button[^>]*>', html_content))
    links = len(re.findall(r'<a\s+href', html_content))
    inputs = len(re.findall(r'<input[^>]*>', html_content))
    total_interactive = buttons + links + inputs
    
    return {
        "check": "keyboard_nav",
        "focus_rules_found": len(focus_rules),
        "has_visible_focus_style": has_visible_focus,
        "interactive_elements": total_interactive,
        "pass": has_visible_focus and total_interactive > 0,
    }


# ---------------------------------------------------------------------------
# Check 3: ARIA LABELS
# ---------------------------------------------------------------------------

def check_aria_labels(html_content):
    """Check that cockpit panels have appropriate labels/headings."""
    # Find all panel-like containers (divs with class containing 'panel' or 'cockpit')
    panels = re.findall(r'<div[^>]*(?:class="[^"]*(?:panel|cockpit)[^"]*")[^>]*>', html_content)
    
    # For each panel, check if it has:
    # - An aria-label or aria-labelledby attribute
    # - A heading element (h1-h6) as first child
    # - Accessible text content
    labeled = 0
    unlabeled = []
    
    for panel in panels:
        has_aria = 'aria-label' in panel or 'aria-labelledby' in panel or 'role=' in panel
        if has_aria:
            labeled += 1
        else:
            # Extract the class/id for reporting
            cls = re.search(r'class="([^"]+)"', panel)
            unlabeled.append(cls.group(1) if cls else "unknown")
    
    # Check buttons have accessible text (not just icons)
    buttons_no_text = []
    for m in re.finditer(r'<button([^>]*)>(.*?)</button>', html_content, re.DOTALL):
        attrs = m.group(1)
        content = m.group(2).strip()
        # Strip HTML tags to get text
        text_only = re.sub(r'<[^>]+>', '', content).strip()
        has_aria_label = 'aria-label' in attrs
        has_title = 'title=' in attrs  # WCAG: title provides accessible name fallback
        if not text_only and not has_aria_label and not has_title:
            buttons_no_text.append(attrs.strip()[:40] or "(no attrs)")
    
    return {
        "check": "aria_labels",
        "panels_found": len(panels),
        "panels_labeled": labeled,
        "panels_unlabeled": unlabeled,
        "buttons_without_text_or_aria": buttons_no_text,
        "pass": len(buttons_no_text) == 0,  # ARIA on panels is best-effort; buttons must have text/label
    }


# ---------------------------------------------------------------------------
# Full gate run
# ---------------------------------------------------------------------------

def run_gate():
    """Run the full cockpit a11y gate."""
    results = {"ts": now_iso(), "checks": [], "overall_pass": True}
    
    if not INDEX_HTML.exists():
        results["checks"].append({"check": "html_exists", "pass": False, "error": str(INDEX_HTML)})
        results["overall_pass"] = False
        return results
    
    html = INDEX_HTML.read_text(encoding="utf-8", errors="replace")
    css_all = ""
    for cf in CSS_FILES:
        if cf.exists():
            css_all += cf.read_text(encoding="utf-8", errors="replace") + "\n"
    
    # Run all 3 checks
    r1 = check_contrast(css_all, html)
    results["checks"].append(r1)
    if not r1["pass"]:
        results["overall_pass"] = False
    
    r2 = check_keyboard_nav(css_all, html)
    results["checks"].append(r2)
    if not r2["pass"]:
        results["overall_pass"] = False
    
    r3 = check_aria_labels(html)
    results["checks"].append(r3)
    if not r3["pass"]:
        results["overall_pass"] = False
    
    # Log result
    import os
    os.makedirs(os.path.dirname(str(RESULTS_FILE)), exist_ok=True)
    with open(str(RESULTS_FILE), 'a') as f:
        f.write(json.dumps(results) + '\n')
    
    return results


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test():
    """Prove both pass and fail branches for each check category."""
    print("=== Cockpit A11y Gate - Self-Test ===\n")
    passed = 0
    failed = 0
    
    # T1: High-contrast pair passes
    print("[T1] Contrast: white on black (ratio=21:1) -> PASS")
    r = contrast_ratio("#ffffff", "#000000")
    t1_pass = r is not None and r >= 4.5
    if t1_pass:
        print(f"  PASS: ratio={r:.2f} >= 4.5")
        passed += 1
    else:
        print(f"  FAIL: ratio={r}")
        failed += 1
    
    # T2: Low-contrast pair fails
    print("\n[T2] Contrast: light gray on white (ratio~1.3:1) -> FAIL")
    r = contrast_ratio("#f0f0f0", "#ffffff")
    t2_pass = r is not None and r < 4.5
    if t2_pass:
        print(f"  PASS: ratio={r:.2f} < 4.5 (correctly flagged)")
        passed += 1
    else:
        print(f"  FAIL: ratio={r} unexpectedly high")
        failed += 1
    
    # T3: CSS with :focus style -> keyboard nav passes
    print("\n[T3] Keyboard nav: CSS has :focus { outline: 2px solid } -> PASS")
    css_good = ".btn:focus { outline: 2px solid #007bff; }"
    r = check_keyboard_nav(css_good, "<button>Click</button>")
    t3_pass = r["pass"] and r["has_visible_focus_style"]
    if t3_pass:
        print(f"  PASS: focus style detected")
        passed += 1
    else:
        print(f"  FAIL: {r}")
        failed += 1
    
    # T4: CSS without :focus -> keyboard nav fails
    print("\n[T4] Keyboard nav: no focus styles -> FAIL")
    css_bad = ".btn { color: red; }"
    r = check_keyboard_nav(css_bad, "<button>Click</button>")
    t4_pass = not r["pass"] and not r["has_visible_focus_style"]
    if t4_pass:
        print(f"  PASS: correctly detected missing focus styles")
        passed += 1
    else:
        print(f"  FAIL: {r}")
        failed += 1
    
    # T5: ARIA labels - buttons with text pass
    print("\n[T5] ARIA: buttons with text content -> PASS")
    html_good = "<div class='panel'><button>Submit</button><button aria-label='Close'>×</button></div>"
    r = check_aria_labels(html_good)
    t5_pass = r["pass"] and len(r["buttons_without_text_or_aria"]) == 0
    if t5_pass:
        print(f"  PASS: no unlabeled buttons")
        passed += 1
    else:
        print(f"  FAIL: {r}")
        failed += 1
    
    # T6: ARIA labels - button with only icon (no text, no aria-label) -> fails
    print("\n[T6] ARIA: button with only SVG icon, no label -> FAIL")
    html_bad = '<div id="cockpit"><div class="fleet-panel"><button><svg viewBox="0 0 24 24"><path d="M1 1h22v22H1z"/></svg></button></div></div>'
    r = check_aria_labels(html_bad)
    t6_pass = not r["pass"] and len(r["buttons_without_text_or_aria"]) > 0
    if t6_pass:
        print(f"  PASS: {len(r['buttons_without_text_or_aria'])} unlabeled button(s) detected")
        passed += 1
    else:
        print(f"  FAIL: {r}")
        failed += 1
    
    # Summary
    all_pass = failed == 0
    print(f"\n=== SELF-TEST RESULT: {passed} PASS / {failed} FAIL ===")
    return 0 if all_pass else 1


def main():
    parser = argparse.ArgumentParser(description="Cockpit A11y Gate (WCAG AA)")
    parser.add_argument("--self-test", action="store_true", help="Run self-test (6 tests)")
    args = parser.parse_args()
    
    if args.self_test:
        sys.exit(self_test())
    
    result = run_gate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["overall_pass"] else 1)


if __name__ == "__main__":
    main()