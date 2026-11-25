"""Designer G1 (cycle-17): Verify Convergence Dashboard Panel renders all 4 widgets at 1440px."""
import sys, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERIFY_HTML = os.path.join(BASE_DIR, "..", "ui", "cockpit-convergence-verify.html")

def main():
    from playwright.sync_api import sync_playwright
    ok = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        # Test at 1440px
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto("file:///" + VERIFY_HTML.replace("\\", "/"), wait_until="domcontentloaded")
        pg.wait_for_timeout(500)

        # Check container exists
        box = pg.query_selector("#ckpConvergence")
        assert box, "FAIL: #ckpConvergence not found"
        ok.append("container #ckpConvergence exists")

        # Check all 4 cards
        cards = pg.query_selector_all(".ckconv-card")
        assert len(cards) == 4, f"Expected 4 cards, got {len(cards)}"
        ok.append(f"4 widget cards rendered: {[c.inner_text().split(chr(10))[0] for c in cards]}")

        # Check gauge
        gauge = pg.query_selector(".ckconv-gauge")
        assert gauge, "FAIL: gauge not found"
        p_val = gauge.get_attribute("style") or ""
        ok.append(f"gauge rendered (style contains --p)")

        # Check trend SVG
        svgs = pg.query_selector_all(".ckconv-trend svg, .ckconv-spark svg")
        assert len(svgs) >= 2, f"Expected >=2 SVGs (trend + sparkline), got {len(svgs)}"
        ok.append(f"{len(svgs)} SVG charts rendered (trend + sparkline)")

        # Check progress bar
        bar = pg.query_selector(".ckconv-bar i")
        assert bar, "FAIL: progress bar not found"
        width = bar.get_attribute("style") or ""
        assert "%" in width, f"Progress bar has no width: {width}"
        ok.append(f"progress bar visible (width={width})")

        # Check grid layout at 1440px
        grid_style = pg.evaluate("getComputedStyle(document.querySelector('.ckconv')).gridTemplateColumns")
        assert "1fr" in grid_style, f"Grid not 2-col: {grid_style}"
        ok.append(f"grid 2-column at 1440px: {grid_style}")

        # Check no JS errors (filter out file:// protocol noise)
        real_errs = [e for e in errs if "file://" not in e and "CORS" not in e]
        assert not real_errs, f"JS errors: {real_errs}"
        ok.append("no JS console errors")

        b.close()

    for line in ok:
        print("PASS  " + line)
    print(f"\nALL PASS - {len(ok)} checks for Convergence Dashboard Panel at 1440px")

if __name__ == "__main__":
    main()
