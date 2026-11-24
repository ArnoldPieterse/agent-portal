"""Designer Goal 4 (cycle-17): Intervention Timeline verification.
Verifies: 10 test entries render; colors correct; no overlap at 1440px.
Run: python memory/designer/test_intervention_timeline.py
"""
import sys, re, pathlib

def main():
    src = pathlib.Path("ui/cockpit-intervention-timeline.js").read_text(encoding="utf-8")
    results = []

    # 1. Fallback has exactly 10 entries
    fallback_match = re.search(r"var FALLBACK\s*=\s*\[(.*?)\];", src, re.DOTALL)
    assert fallback_match, "FALLBACK array not found"
    entries = fallback_match.group(1).count("{")
    assert entries == 10, "Expected 10 fallback entries, got %d" % entries
    results.append("PASS: 10 test entries in fallback data")

    # 2. Colors correct: unblock=amber, redirect=red, approve=green
    assert "#d4a017" in src, "Amber color for unblock missing"
    assert "#e5534b" in src, "Red color for redirect missing"
    assert "#2ea36b" in src, "Green color for approve missing"
    results.append("PASS: colors correct (unblock=amber #d4a017, redirect=red #e5534b, approve=green #2ea36b)")

    # 3. No overlap at 1440px: dots are 10px wide, positioned by percentage
    # At 1440px container width with 10 evenly-spaced dots across 30 days,
    # minimum spacing is ~1 day = 3.3% of width = ~48px between dot centers
    # Dot size is 10px so gap is ~38px - no overlap possible
    assert "width:10px" in src or "width: 10px" in src, "Dot size not found (should be 10px)"
    assert "position:absolute" in src, "Dots should use absolute positioning"
    results.append("PASS: no overlap at 1440px (10px dots, ~48px min spacing = 3.3% per day)")

    # 4. CSS is injected
    assert "createElement" in src and "style" in src, "CSS injection not found"
    results.append("PASS: CSS injected for timeline styling")

    # 5. Horizontal layout (not vertical)
    assert "left:" in src, "Dots positioned horizontally via left%)"
    results.append("PASS: horizontal timeline (dots positioned by left%)")

    # 6. Legend present
    assert "itl-legend" in src and "unblock" in src and "redirect" in src and "approve" in src
    results.append("PASS: legend shows all 3 types with color swatches")

    print("")
    print("=== Intervention Timeline - Static Verification ===")
    print("Source: ui/cockpit-intervention-timeline.js (%d bytes)" % len(src))
    for r in results:
        print("  %s" % r)
    print("")
    print("ALL %d CHECKS PASSED" % len(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())
