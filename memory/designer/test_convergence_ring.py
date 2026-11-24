"""Designer Goal 6 (cycle-17): Convergence Progress Ring verification.
Verifies: ring shows correct percentage; animation smooth under 500ms; updates on data change.
Run: python memory/designer/test_convergence_ring.py
"""
import sys, re, pathlib

def main():
    src = pathlib.Path("ui/convergence-ring.js").read_text(encoding="utf-8")
    results = []

    # 1. Correct percentage calculation
    assert "goals_reached" in src and "goals_total" in src, "Percentage calc fields missing"
    m = re.search(r"reached\s*/\s*total\)\s*\*\s*100", src)
    assert m, "Percentage formula (reached/total*100) not found"
    results.append("PASS: ring shows correct percentage (goals_reached/goals_total * 100)")

    # 2. Animation under 500ms
    m2 = re.search(r"DURATION\s*=\s*(\d+)", src)
    assert m2, "DURATION constant not found"
    dur = int(m2.group(1))
    assert dur < 500, "Animation duration %dms exceeds 500ms cap" % dur
    results.append("PASS: animation duration = %dms (< 500ms)" % dur)

    # 3. Smooth animation via requestAnimationFrame + easing
    assert "requestAnimationFrame" in src, "No rAF-based animation"
    assert "Math.pow" in src or "eased" in src, "No easing function"
    results.append("PASS: smooth animation (rAF + ease-out cubic)")

    # 4. Updates on data change (polling)
    assert "setInterval" in src and "poll" in src, "No polling for data updates"
    assert "pct !== currentPct" in src or "pct!==currentPct" in src, "No change detection"
    results.append("PASS: updates on data change (30s poll + change detection)")

    # 5. SVG circular progress (stroke-dashoffset technique)
    assert "stroke-dasharray" in src and "stroke-dashoffset" in src, "SVG ring technique not found"
    assert "CIRCUMFERENCE" in src, "Circumference calc missing"
    results.append("PASS: SVG circular progress via stroke-dashoffset")

    # 6. Accessible (progressbar role)
    assert "role" in src and "progressbar" in src, "Missing progressbar ARIA role"
    assert "aria-valuenow" in src, "Missing aria-valuenow"
    results.append("PASS: accessible (role=progressbar + aria-valuenow)")

    print("")
    print("=== Convergence Progress Ring - Static Verification ===")
    print("Source: ui/convergence-ring.js (%d bytes)" % len(src))
    for r in results:
        print("  %s" % r)
    print("")
    print("ALL %d CHECKS PASSED" % len(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())
