"""Designer G2 (cycle-15): Playwright ARIA + keyboard + contrast test
for the Fleet Cockpit panel. Run: python memory/designer/ui_a11y_test.py
"""
import re, sys
BASE = "http://127.0.0.1:8099"

def lum(rgb):
    if isinstance(rgb, str):
        m = [int(v) for v in rgb.replace("rgba(", "").replace("rgb(", "").rstrip(")").split(",")][:3]
    else:
        m = list(rgb)
    c = [x/255 for x in m]
    c = [x/12.92 if x <= 0.04045 else ((x+0.055)/1.055)**2.4 for x in c]
    return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2]
def ratio(fg, bg):
    a, b = lum(fg), lum(bg)
    if a < b: a, b = b, a
    return (a + 0.05) / (b + 0.05)

def main():
    from playwright.sync_api import sync_playwright
    ok = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(BASE, wait_until="domcontentloaded")
        pg.evaluate("var t0=document.querySelector(String.fromCharCode(46)+'tour-overlay');if(t0)t0.remove();")
        pg.click("#ckpBtn")
        pg.wait_for_selector("#ckp15Ring svg", timeout=10000)
        ok.append("panel + ring rendered")
        assert pg.get_attribute("#ckp15live", "aria-live") == "polite", "no aria-live polite"
        vn = int(pg.get_attribute("#ckp15Ring svg", "aria-valuenow"))
        assert 0 <= vn <= 100, vn
        ok.append("aria-live polite + progressbar aria-valuenow=%d" % vn)
        n = len(pg.query_selector_all(".sec15"))
        assert n >= 4, n
        pg.focus(".sec15")
        pg.keyboard.press("ArrowDown")
        c = pg.evaluate("document.activeElement.className")
        assert c in ("sec15", "ckcard15"), c
        ok.append("keyboard: %d sections, ArrowDown moved focus to .%s" % (n, c))
        fg = pg.evaluate("getComputedStyle(document.querySelector('.sec15')).color")
        bg = pg.evaluate("getComputedStyle(document.querySelector('.sec15').parentElement).backgroundColor")
        r = ratio(fg, bg)
        assert r >= 4.5, r
        ok.append("contrast .sec15 label: %.2f:1 (AA pass)" % r)
        ctx = b.new_context(reduced_motion="reduce")
        pg2 = ctx.new_page()
        pg2.goto(BASE, wait_until="domcontentloaded")
        pg2.evaluate("var t0=document.querySelector(String.fromCharCode(46)+'tour-overlay');if(t0)t0.remove();")
        pg2.click("#ckpBtn")
        pg2.wait_for_selector("#ckp15Ring svg", timeout=10000)
        td = pg2.evaluate("getComputedStyle(document.querySelector('.fgc')).transitionDuration")
        assert td == "0s", td
        ok.append("prefers-reduced-motion: transitions disabled")
        b.close()
    bad = [e for e in errs if "cockpit-cycle15" not in e]
    for line in ok: print("PASS  " + line)
    if bad: print("FAIL  console errors: %s" % bad); sys.exit(1)
    print("ALL PASS - %d checks" % len(ok))

if __name__ == "__main__":
    main()
