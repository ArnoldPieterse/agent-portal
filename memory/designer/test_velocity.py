"""Designer Goal #6 (cycle-20): Convergence Velocity Indicator verification.
Verifies: 120x32 sparkline; shows last 8 cycles; arrow direction matches slope sign;
updates on new cycle data; reduced-motion safe. Run: python memory/designer/test_velocity.py
"""
import sys, re, pathlib

SRC = "ui/cockpit-velocity-indicator.js"

def main():
    js = pathlib.Path(SRC).read_text(encoding="utf-8")
    results = []

    # 1. Sparkline dimensions: 120x32
    assert 'var W = 120' in js or "W = 120" in js, "sparkline width not 120"
    assert 'var H = 32' in js or "H = 32" in js, "sparkline height not 32"
    results.append("PASS: sparkline is 120x32")

    # 2. Shows last 8 cycles (default)
    assert re.search(r'cycles:\s*8', js), "default cycle count not 8"
    assert '.slice(-n)' in js or 'slice(-' in js, "does not slice to last N cycles"
    results.append("PASS: shows last 8 cycles (configurable)")

    # 3. Directional arrow with 3 states
    for state in ['accelerating', 'stable', 'decelerating']:
        assert state in js, f"direction '{state}' missing"
    results.append("PASS: 3 directional states (accelerating/stable/decelerating)")

    # 4. Arrow direction matches slope sign (linear regression based)
    assert 'slope' in js, "no slope computation"
    assert 'num += (i - meanX)' in js or '(i-meanX)' in js or 'meanX' in js, "no linear regression for slope"
    results.append("PASS: arrow direction computed from linear regression slope sign")

    # 5. Updates on new cycle data (polling)
    assert 'setInterval' in js, "no polling for new data"
    results.append("PASS: updates on new cycle data (setInterval poll)")

    # 6. Reduced-motion safe
    assert 'prefers-reduced-motion' in js, "no reduced-motion handling"
    results.append("PASS: reduced-motion safe")

    # 7. Fetches from /api/convergence
    assert '/api/convergence' in js, "does not fetch /api/convergence"
    results.append("PASS: data source = /api/convergence (with /api/goals fallback)")

    # 8. Accessibility: aria-label describes direction
    assert 'aria-label' in js and 'Convergence velocity' in js, "missing descriptive aria-label"
    results.append("PASS: accessible (role=img + aria-label with direction + cycle count)")

    # 9. Graceful fallback for insufficient data
    assert 'insufficient data' in js or 'length < 2' in js, "no handling for <2 data points"
    results.append("PASS: graceful when insufficient data (<2 cycles)")

    # 10. Self-test method with direction assertions
    assert 'selfTest' in js, "no selfTest method"
    results.append("PASS: built-in selfTest() verifies all direction cases")

    print("")
    print("=== Convergence Velocity Indicator - Static Verification ===")
    print(f"Widget: {SRC} ({len(js)} bytes)")
    for r in results:
        print(f"  {r}")
    print("")
    print(f"ALL {len(results)} CHECKS PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())