#!/usr/bin/env python3
"""WCAG AA contrast checker - LIVE parser for ui/app.css (Designer goal #2 evidence).

Supersedes the hard-coded palette in contrast_check_goal2.py: it reads the actual
token values from disk each run, so a token-layer change (goal #1) can never make
this report stale. Future-proof: auto-detects any [data-theme="..."] block, so when
the light theme lands it is checked with zero code changes.

Rule: memory/portal/file-modularity.md | sibling: contrast_check_goal2.py (deprecated, stale palette)
Usage: python memory/designer/wcag_contrast_live.py
Output: table to stdout + JSON evidence at memory/designer/wcag_contrast_live_<YYYYMMDD>.json
"""
import re, sys, json, datetime

CSS = "ui/app.css"
AA_NORMAL = 4.5   # WCAG 2.x AA, normal text
AA_LARGE = 3.0    # WCAG 2.x AA, large text (>=18pt / 14pt bold)

# semantic token -> (foreground, background) pairs to test for readable text
PAIRS = [
    ("text", "bg"), ("dim", "bg"), ("faint", "bg"),
    ("acc", "bg"), ("ok", "bg"), ("warn", "bg"), ("err", "bg"),
    ("text", "panel"), ("dim", "panel"), ("faint", "panel"),
    ("acc", "panel"), ("ok", "panel"), ("warn", "panel"), ("err", "panel"),
]

HEX = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

def parse_hex(v):
    m = HEX.match(v.strip())
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def extract_blocks(css):
    """Return {theme_name: {token: rgb}} for :root and every [data-theme=...]."""
    themes = {}
    # :root -> 'dark' (current portal default)
    m = re.search(r":root\s*\{([^}]*)\}", css)
    if m:
        themes["dark"] = _tokens(m.group(1))
    for t in re.finditer(r"\[data-theme=\"?([a-z-]+)\"?\]\s*\{([^}]*)\}", css):
        themes[t.group(1)] = _tokens(t.group(2))
    return themes

def _tokens(body):
    out = {}
    for name, val in re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", body):
        rgb = parse_hex(val)
        if rgb:
            out[name.lstrip("-")] = rgb
    return out

def luminance(rgb):
    def s(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (s(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

def main():
    css = open(CSS, encoding="utf-8").read()
    themes = extract_blocks(css)
    stamp = datetime.date.today().strftime("%Y-%m-%d")
    report = {"date": stamp, "source": CSS, "thresholds": {"AA_normal": AA_NORMAL, "AA_large": AA_LARGE}, "themes": {}}
    all_pass = bool(themes)

    print(f"WCAG AA contrast check - live parse of {CSS} ({stamp})")
    print("Themes found:", ", ".join(sorted(themes)) or "(none)")
    if not themes:
        print("RESULT: FAIL - no color tokens parsed from CSS")
        sys.exit(1)

    for theme, toks in sorted(themes.items()):
        rows = []
        theme_pass = True
        for fg, bg in PAIRS:
            if fg not in toks or bg not in toks:
                continue  # token absent in this theme -> skip, not a failure
            ratio = contrast(toks[fg], toks[bg])
            ok = ratio >= AA_NORMAL
            theme_pass &= ok
            rows.append({"pair": f"{fg}/{bg}", "ratio": round(ratio, 2),
                         "aa_normal": ok, "aa_large": ratio >= AA_LARGE})
        report["themes"][theme] = {"tokens": len(toks), "pairs_tested": len(rows),
                                   "pass": theme_pass, "rows": rows}
        all_pass &= theme_pass
        print(f"\n[{theme}]  {len(toks)} color tokens, {len(rows)} pairs tested -> {'PASS' if theme_pass else 'FAIL'}")
        print(f"{'pair':<14}{'ratio':>7}  AA(4.5)  AA-large(3.0)")
        for r in rows:
            flag = "ok" if r["aa_normal"] else ("large-only" if r["aa_large"] else "FAIL")
            print(f"{r['pair']:<14}{r['ratio']:>7.2f}   {'PASS' if r['aa_normal'] else 'fail':<6}  {flag}")

    # honest note on missing light theme
    if "light" not in themes:
        report["note"] = "light theme tokens not present in ui/app.css yet (goal #1 token layer); only dark checked."
        print("\nnote: no [data-theme=\"light\"] block found - light theme not implemented yet.")

    out = f"memory/designer/wcag_contrast_live_{datetime.date.today().strftime('%Y%m%d')}.json"
    json.dump(report, open(out, "w", encoding="utf-8"), indent=2)
    print(f"\nevidence -> {out}")
    print("RESULT:", "ALL PASS (WCAG AA >=4.5:1) in all themes present" if all_pass else "FAILURES DETECTED")
    sys.exit(0 if all_pass else 1)

if __name__ == "__main__":
    main()
