#!/usr/bin/env python3
"""css_drift_subcheck.py - Drop-in CSS drift sub-check for Forge's drift_detect.py.

Exposes run_css_drift_check() returning a dict compatible with the main
report shape. Add one call inside detect_drift():

    # Check 4: CSS orphan selectors (Pixel)
    from memory.pixel.css_drift_subcheck import run_css_drift_check
    css = run_css_drift_check()
    if css.get('new_orphans'):
        report['detail'].append(f"CSS DRIFT: {', '.join(sorted(css['new_orphans']))}")
        has_drift = True

Or inline (no import path issues):

    # Check 4: CSS orphan selectors
    css_result = _css_drift_inline()
    if css_result.get('new_orphans'):
        report['detail'].append(f"CSS DRIFT: {', '.join(sorted(css_result['new_orphans']))}")
        has_drift = True

Verify: python memory/pixel/css_drift_subcheck.py  (exit 0=clean, 1=new drift)
"""
import re, pathlib, sys, json
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BASELINE_PATH = ROOT / "memory" / "pixel" / "css_baseline.json"  # shared with css_drift_check.py
CSS_PATH = ROOT / "ui" / "app.css"
HTML_PATH = ROOT / "index.html"
JS_FILES = [ROOT / "ui" / f for f in ("core.js", "uploads.js")]


def _extract_css_classes(css_text: str) -> set:
    classes = set(re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', css_text))
    return {c for c in classes if not re.match(r'^\d', c)}


def _extract_references(html_text: str, js_text: str) -> set:
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


def run_css_drift_check() -> dict:
    """Return {new_orphans: set, total_classes: int}.
    
    Uses the same baseline logic as css_drift_check.py: stores ALL CSS classes
    at baseline time. New orphans = current orphans NOT in the baseline class set.
    new_orphans empty = no drift.
    """
    css_text = CSS_PATH.read_text(encoding='utf-8')
    html_text = HTML_PATH.read_text(encoding='utf-8')
    js_text = '\n'.join(f.read_text(encoding='utf-8') for f in JS_FILES if f.exists())

    classes = _extract_css_classes(css_text)
    refs = _extract_references(html_text, js_text)
    current_orphans = classes - refs

    # Load baseline: set of ALL CSS classes at last known-good state
    baseline_classes = set()
    if BASELINE_PATH.exists():
        data = json.loads(BASELINE_PATH.read_text(encoding='utf-8'))
        baseline_classes = set(data.get('css_classes', []))

    new_orphans = current_orphans - baseline_classes

    return {
        'new_orphans': new_orphans,
        'total_classes': len(classes),
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


def main():
    result = run_css_drift_check()
    if result['new_orphans']:
        print(f"[css-drift-subcheck] FAIL: {len(result['new_orphans'])} new orphan selectors: "
              f"{', '.join(sorted(result['new_orphans']))}")
        sys.exit(1)
    else:
        print(f"[css-drift-subcheck] PASS: no new orphans ({result['total_classes']} classes).")
        sys.exit(0)


if __name__ == '__main__':
    main()