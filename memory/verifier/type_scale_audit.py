#!/usr/bin/env python
"""Static typography-scale audit for Designer Goal 7.

Acceptance test (designer.md #7): computed styles show 0 violations of the
5-step scale: h1=24px, h2=18px, h3=15px, body=14px, caption=12px.

This is a STATIC proxy for the computed-style audit (CDP/headless not
available in sandbox): it extracts every `font-size:` declaration from
ui/*.css and flags any value off the allowed scale. A PASS here is strong
evidence but NOT a substitute for a live DevTools check — noted in output.

Usage:  python memory/verifier/type_scale_audit.py
Exit:   0 = 0 violations (PASS), 1 = violations found (FAIL), 2 = no css files
"""
import os, re, sys

# Allowed scale per goal text. rem/em are NOT in the spec -> flagged.
ALLOWED_PX = {24, 18, 15, 14, 12}
ROOT_PX_DEFAULT = 16  # for resolving rem if we ever allow them

CSS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ui")
FONT_SIZE_RE = re.compile(r'font-size\s*:\s*([^;{}]+)')


def parse_value(raw):
    """Return (px, kind) for a single font-size value, or None if unparseable."""
    raw = raw.strip()
    m = re.fullmatch(r'([\d.]+)\s*(px|rem|em|%|pt)', raw)
    if not m:
        return None
    num, unit = float(m.group(1)), m.group(2)
    if unit == 'px':
        return (num, 'px')
    if unit in ('rem', 'em'):
        return (num * ROOT_PX_DEFAULT, unit)
    return None  # %/pt not on a fixed px scale -> treat as violation via caller


def main():
    css_dir = os.path.normpath(CSS_DIR)
    files = [os.path.join(css_dir, f) for f in sorted(os.listdir(css_dir))
             if f.endswith('.css')] if os.path.isdir(css_dir) else []
    if not files:
        print(f"FAIL: no .css files found under {css_dir}")
        return 2

    total = 0
    violations = []
    on_scale = 0
    for path in files:
        rel = os.path.relpath(path)
        with open(path, encoding='utf-8', errors='replace') as fh:
            for lineno, line in enumerate(fh, 1):
                for m in FONT_SIZE_RE.finditer(line):
                    total += 1
                    raw = m.group(1).strip()
                    parsed = parse_value(raw)
                    if parsed is None:
                        violations.append(f"{rel}:{lineno}: font-size:{raw!r} (unparseable/non-px unit)")
                        continue
                    px, kind = parsed
                    if kind != 'px' or px not in ALLOWED_PX:
                        violations.append(f"{rel}:{lineno}: font-size:{raw!r} -> {px:g}px (off scale {sorted(ALLOWED_PX)})")
                    else:
                        on_scale += 1

    print("=== Typography Scale Audit (Designer Goal 7) ===")
    print(f"Files scanned : {len(files)} ({', '.join(os.path.relpath(p) for p in files)})")
    print(f"font-size decls: {total} total, {on_scale} on-scale, {len(violations)} off-scale")
    if violations:
        print(f"\nFAIL: {len(violations)} violation(s):")
        for v in violations:
            print("  - " + v)
        print("\nNOTE: static CSS audit (CDP unavailable); a live DevTools computed-style check is the formal acceptance test, this is strong proxy evidence.")
        return 1
    print("\nPASS: 0 off-scale font-size values. All font-size declarations are on the 5-step scale.")
    print("NOTE: static CSS audit (CDP unavailable); a live DevTools computed-style check is the formal acceptance test, this is strong proxy evidence.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
