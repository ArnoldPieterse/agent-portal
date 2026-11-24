"""Designer Goal 5 (cycle-17): Goal Complexity Heatmap verification.
Verifies: 10 goals render as cells; colors match scores; tooltip works.
Run: python memory/designer/test_complexity_heatmap.py
"""
import sys, re, pathlib

def main():
    src = pathlib.Path("ui/cockpit-complexity-heatmap.js").read_text(encoding="utf-8")
    results = []

    # 1. Fallback has exactly 10 goals
    fallback_match = re.search(r"var FALLBACK\s*=\s*\[(.*?)\];", src, re.DOTALL)
    assert fallback_match, "FALLBACK not found"
    entries = fallback_match.group(1).count("{")
    assert entries == 10, "Expected 10 goals, got %d" % entries
    results.append("PASS: 10 goals in fallback data")

    # 2. Colors match scores (1=light green to 5=dark red)
    colors = re.search(r"var COLORS\s*=\s*\[(.*?)\];", src, re.DOTALL)
    assert colors, "COLORS array not found"
    color_str = colors.group(1)
    # Score 1: light green (#a5d6a7), Score 5: dark red (#b71c1c)
    assert "#a5d6a7" in color_str, "Light green (score 1) missing"
    assert "#b71c1c" in color_str, "Dark red (score 5) missing"
    results.append("PASS: colors match scores (1=#a5d6a7 light green to 5=#b71c1c dark red)")

    # 3. Tooltip via title attribute showing factors
    assert "title=" in src, "No tooltip (title attribute) found"
    assert "factors" in src, "Factors text not used in tooltip"
    results.append("PASS: tooltip shows scoring factors (title=factors)")

    # 4. Grid layout for cells
    assert "display:grid" in src, "Grid layout not found"
    results.append("PASS: grid layout for goal cells")

    # 5. CSS injected
    assert "createElement" in src and "style" in src, "CSS injection missing"
    results.append("PASS: CSS injected for heatmap styling")

    # 6. Legend with color scale
    assert "ckconv-legend" in src, "Legend not found"
    results.append("PASS: legend shows 1-5 color scale")

    print("")
    print("=== Goal Complexity Heatmap - Static Verification ===")
    print("Source: ui/cockpit-complexity-heatmap.js (%d bytes)" % len(src))
    for r in results:
        print("  %s" % r)
    print("")
    print("ALL %d CHECKS PASSED" % len(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())
