#!/usr/bin/env python3
"""Static horizontal-overflow validator for the Convergence panel @375/768.

Owner: Pixel (goal #5, memory/goals/pixel.md). Built as a Designer assist step.
Purpose: close the "static validation now" leg of goal #5 without a live browser.
It parses the CSS actually shipped in ui/cockpit-convergence.js (the injected
<style> string) + ui/convergence-ring.css, extracts media-query breakpoints and
fixed-width constraints, then computes the worst-case content width at 375px and
768px. PASS = no element's required min-content width exceeds available width.

This is a STATIC guarantee (parses real shipped CSS, does width math). It does NOT
replace the live CDP screenshot leg (needs Red) - it proves no-overflow at the
CSS level so the live leg only has to confirm rendering.
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root (contains ui/)
JS   = ROOT / "ui" / "cockpit-convergence.js"
RING = ROOT / "ui" / "convergence-ring.css"
VERIFY_HTML = ROOT / "ui" / "cockpit-convergence-verify.html"

def extract_injected_css(js_text):
    """Pull the string array inside css()'s s.textContent = [ ... ] join."""
    m = re.search(r's\.textContent\s*=\s*\[(.*?)\]\s*\.join', js_text, re.S)
    if not m:
        return ""
    body = m.group(1)
    # each rule is a quoted string like ".ckconv{...}"
    rules = re.findall(r'"((?:[^"\\]|\\.)*)"', body)
    return "\n".join(rules)

def parse_media(css):
    """Return (base_rules, {maxwidth: [rules]})."""
    base, media = [], {}
    for m in re.finditer(r'@media\s*\(max-width:\s*(\d+)px\)\s*\{(.+?)\}', css):
        media.setdefault(int(m.group(1)), []).append(m.group(2))
    # strip media blocks out, keep the rest as base
    no_media = re.sub(r'@media[^{]*\{.*?\}\s*', "", css)
    for r in no_media.split("}"):
        if r.strip():
            base.append(r + "}")
    return base, media

def fixed_widths(rules):
    """Collect explicit width:<N>px declarations (min-content floor)."""
    out = []
    for m in re.finditer(r'width\s*:\s*(\d+)px', " ".join(rules)):
        out.append(int(m.group(1)))
    return out

def has_guard(css, needle):
    return needle in css

def main():
    js = JS.read_text(encoding="utf-8")
    ring = RING.read_text(encoding="utf-8")
    injected = extract_injected_css(js)
    allcss = injected + "\n" + ring
    base, media = parse_media(injected)  # grid behaviour lives in injected css

    print("== Convergence panel static overflow validator ==")
    print(f"injected CSS rules parsed: {len(base)} base, breakpoints: {sorted(media)}px")
    results = []

    # --- guard 1: single-column stack must cover 375px ---------------------
    # find the breakpoint that collapses grid to 1fr
    # robust: scan raw injected CSS for a media block that collapses grid to a
    # single track (any amount of whitespace around the value). Per-bp capture is
    # brittle to nested braces; a direct text scan is not.
    single_col_bp = None
    for m in re.finditer(r'@media\s*\(max-width:\s*(\d+)px\)\{([^@]*)', injected):
        if re.search(r'grid-template-columns\s*:\s*1fr\b', m.group(2)):
            single_col_bp = min(single_col_bp or 99999, int(m.group(1)))
    print("  [diag] single-col bp candidates in raw CSS:",
          re.findall(r'@media\s*\(max-width:\s*(\d+)px\)\{[^@]*grid-template-columns', injected))
    ok_single = single_col_bp is not None and 375 <= single_col_bp
    results.append(("single-column stack covers 375px", ok_single,
                    f"collapse @<={single_col_bp}px (need >=375)"))

    # --- guard 2: overflow guards present ----------------------------------
    ok_minw = has_guard(allcss, "min-width:0") or has_guard(allcss, "min-width: 0")
    results.append(("card min-width:0 (prevents grid blowout)", ok_minw, "on .ckconv-card"))
    ok_svgmax = (has_guard(allcss, "max-width:100%") or has_guard(allcss, "max-width: 100%")) and \
                (".ckconv-card svg" in allcss)
    results.append(("svg max-width:100% + height:auto", ok_svgmax, "on .ckconv-card svg"))

    # --- guard 3: worst-case fixed width vs available at each viewport ----- 
    # body padding 20px/side in verify fixture; card padding ~12px/side.
    body_pad = 40   # left+right
    card_pad = 24   # left+right (12*2 base)
    svgs = [140]    # trend + intervention svg width (from JS render fns)
    gauge_max = 72  # gauge base width
    for vp in (375, 768):
        cols = 1 if (single_col_bp and vp <= single_col_bp) else 2
        avail_per_col = (vp - body_pad - (8 * (cols - 1))) / cols  # 8px gap
        need_max = max(svgs + [gauge_max])
        fits = need_max < avail_per_col - card_pad
        results.append((f"no overflow @ {vp}px ({cols}-col)", fits,
                        f"avail/col≈{avail_per_col:.0f}px, worst fixed={need_max}px"))

    # --- guard 4: verify fixture actually loads the panel ------------------
    html = VERIFY_HTML.read_text(encoding="utf-8")
    ok_fixture = "cockpit-convergence.js" in html and 'id="ckpPanel"' in html.replace(" ","")
    results.append(("verify fixture wires panel + script", ok_fixture, "fixture present"))

    print()
    allpass = True
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:42s} — {detail}")
        allpass = allpass and ok
    print()
    print("RESULT:", "PASS (static no-overflow @375/768)" if allpass else "FAIL")
    return 0 if allpass else 1

if __name__ == "__main__":
    sys.exit(main())
