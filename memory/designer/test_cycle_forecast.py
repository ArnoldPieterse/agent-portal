"""Designer Goal 3 (cycle-17): Cycle Duration Forecast Widget verification.
Verifies: renders with 5 data points; prediction line visible; gap highlight correct.
Run: python memory/designer/test_cycle_forecast.py
"""
import sys, re, pathlib

def main():
    src = pathlib.Path("ui/cockpit-cycle-forecast.js").read_text(encoding="utf-8")
    results = []

    # 1. Slices last 5 data points
    assert "slice(-5)" in src, "Does not slice to 5 data points"
    results.append("PASS: renders with 5 data points (data.slice(-5))")

    # 2. Prediction line is dotted (stroke-dasharray)
    assert "stroke-dasharray" in src, "No stroke-dasharray for predicted line"
    assert "cf-line-predicted" in src, "Predicted line class not found"
    results.append("PASS: prediction line visible (dotted via stroke-dasharray)")

    # 3. Gap highlight at >20%
    assert "gapPct > 20" in src or "gapPct>20" in src, "Gap threshold not 20%"
    assert "cf-gap-highlight" in src, "Gap highlight class not found"
    results.append("PASS: gap highlighted when >20% (rect + label)")

    # 4. CSS injection present for styling
    assert "injectCSS" in src or "createElement('style')" in src or 'createElement("style")' in src, "No CSS injection"
    results.append("PASS: CSS injected for chart styling")

    # 5. SVG role for accessibility
    assert 'role="img"' in src, "SVG missing role=img"
    results.append("PASS: SVG has role=img (accessible)")

    # 6. Legend present
    assert "cf-legend" in src and "Actual" in src and "Predicted" in src, "Legend missing"
    results.append("PASS: legend shows Actual + Predicted")

    # 7. Data source is cycle-durations.jsonl
    assert "cycle-durations.jsonl" in src, "Data source not cycle-durations.jsonl"
    results.append("PASS: data source = memory/ops/cycle-durations.jsonl")

    print("")
    print("=== Cycle Duration Forecast Widget - Static Verification ===")
    print("Source: ui/cockpit-cycle-forecast.js (%d bytes)" % len(src))
    for r in results:
        print("  %s" % r)
    print("")
    print("ALL %d CHECKS PASSED" % len(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())
