#!/usr/bin/env python3
"""
css_drift_check.py - CSS selector drift detector for Forge's gate pipeline.

Catches new unreferenced CSS selectors (dead code) introduced by UI changes.
Uses a baseline of known orphans so only NEW drift triggers a failure.

Usage:
    python memory/pixel/css_drift_check.py
Exit: 0 = no new drift, 1 = new orphan selectors detected.

Integration: add to Forge's drift_detect.py as a sub-check after any
commit that touches ui/app.css.
"""
import re, pathlib, sys, json

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # project root

def extract_css_classes(css_text):
    classes = set(re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', css_text))
    return {c for c in classes if not re.match(r'^\d', c)}

def extract_references(html_text, js_text):
    refs = set()
    for group in re.findall(r'class="([^"]*)"', html_text):
        for cn in group.split():
            refs.add(cn)
    for m in re.findall(r"['\"`]([a-zA-Z][a-zA-Z0-9_-]{2,})['\"`]", js_text):
        refs.add(m)
    for m in re.findall(r'class=["\']([^"\']*?)["\']', js_text):
        for cn in m.split():
            refs.add(cn)
    return refs

def main():
    css_path = ROOT / "ui" / "app.css"
    html_path = ROOT / "index.html"
    js_files = [ROOT / "ui" / f for f in ("uploads.js", "core.js")]
    
    css = css_path.read_text(encoding="utf-8")
    html = html_path.read_text(encoding="utf-8")
    js_combined = "".join(f.read_text(encoding="utf-8") + "\n" for f in js_files)
    
    current_classes = extract_css_classes(css)
    refs = extract_references(html, js_combined)
    orphans = current_classes - refs
    
    baseline_path = ROOT / "memory" / "pixel" / "css_baseline.json"
    if not baseline_path.exists():
        # First run: create baseline
        data = {
            "generated": "auto",
            "css_classes": sorted(current_classes),
            "orphans_at_baseline": sorted(orphans),
            "note": "Baseline for css_drift_check.py"
        }
        baseline_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"[css-drift] Baseline created ({len(current_classes)} classes, {len(orphans)} known orphans).")
        return 0
    
    baseline = set(json.loads(baseline_path.read_text(encoding="utf-8")).get("css_classes", []))
    new_orphans = orphans - baseline
    
    if new_orphans:
        print(f"[css-drift] FAIL: {len(new_orphans)} new orphan selector(s) detected:")
        for o in sorted(new_orphans):
            idx = css.find("." + o)
            line_no = css[:idx].count("\n") + 1 if idx >= 0 else "?"
            print(f"  .{o}  (app.css line ~{line_no})")
        print("Fix: add the missing JS/HTML reference, or remove the dead CSS rule.")
        return 1
    
    # Also flag classes REMOVED from CSS but still in baseline (informational)
    removed = baseline - current_classes
    if removed:
        print(f"[css-drift] INFO: {len(removed)} class(es) removed since baseline (OK if intentional):")
        for o in sorted(removed):
            print(f"  .{o}")
    
    print("[css-drift] PASS: no new orphan selectors.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
