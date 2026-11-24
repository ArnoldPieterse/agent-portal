"""Designer Goal 2 (cycle-17): Steady-State Visual Indicator verification.
Verifies: mode change triggers visual within 1s; no layout shift.
Strategy: static code analysis (no browser needed) + logic assertions.
Run: python memory/designer/test_steady_state_indicator.py
"""
import sys, re, pathlib

def main():
    src = pathlib.Path("ui/cockpit-calm-mode.js").read_text(encoding="utf-8")
    results = []

    # 1. Transition time < 1000ms
    m = re.search(r"TRANSITION_MS\s*=\s*(\d+)", src)
    assert m, "TRANSITION_MS constant not found"
    ms = int(m.group(1))
    assert ms < 1000, "Transition time %dms exceeds 1s cap" % ms
    results.append("PASS: transition time = %dms (< 1000ms)" % ms)

    # 2. Green border via box-shadow (no layout shift)
    assert "box-shadow" in src, "No box-shadow found for green border"
    assert "rgba(90,138,114" in src, "Green color not present in box-shadow"
    results.append("PASS: green border uses box-shadow (no layout shift)")

    # 3. Converged badge text
    assert '"Converged"' in src or "'Converged'" in src, "Badge text 'Converged' not found"
    results.append("PASS: 'Converged' badge text present")

    # 4. Badge uses inline-flex (minimal layout impact)
    assert "inline-flex" in src, "Badge should use display:inline-flex"
    results.append("PASS: badge uses display:inline-flex (no layout shift)")

    # 5. Reduced animation in calm mode
    assert "animation-duration" in src and "!important" in src, "Reduced animation not found"
    results.append("PASS: reduced animation via !important override")

    # 6. Amber pulse on exit
    assert "amber-pulse" in src, "Amber pulse keyframe not found"
    assert "mode-exit-pulse" in src, "Exit pulse class not applied"
    assert "rgba(212,160,23" in src, "Amber color not present"
    results.append("PASS: amber pulse on exit (keyframes + class toggle)")

    # 7. Pulse auto-removes after animation
    m2 = re.search(r"setTimeout.*mode-exit-pulse", src, re.DOTALL)
    assert m2, "Amber pulse cleanup setTimeout not found"
    results.append("PASS: amber pulse auto-removed via setTimeout")

    # 8. No border-width changes (layout shift guard)
    css_block = src[src.find("injectCSS"):src.find("function setMode")]
    assert "border-width" not in css_block, "border-width change causes layout shift"
    results.append("PASS: no border-width changes at container level")

    # 9. prefers-reduced-motion respected
    assert "prefers-reduced-motion" in src, "Reduced motion preference not handled"
    results.append("PASS: prefers-reduced-motion media query present")

    # 10. Exposes test API for Playwright (for future live tests)
    assert "window.__calmMode" in src, "Test API not exposed"
    results.append("PASS: window.__calmMode test API exposed for Playwright")

    print("")
    print("=== Steady-State Visual Indicator - Static Verification ===")
    print("Source: ui/cockpit-calm-mode.js (%d bytes)" % len(src))
    for r in results:
        print("  %s" % r)
    print("")
    print("ALL %d CHECKS PASSED" % len(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())
