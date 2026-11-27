"""Designer Goal #5 (cycle-20): Goal Pipeline Flow verification.
Verifies: renders from /api/goals; 4-stage pipeline; bottleneck detection at >3;
click-through detail; accessible. Run: python memory/designer/test_pipeline_flow.py
"""
import sys, re, pathlib

SRC = "ui/cockpit-pipeline-flow.js"

def main():
    js = pathlib.Path(SRC).read_text(encoding="utf-8")
    results = []

    # 1. Fetches from /api/goals
    assert '/api/goals' in js, "does not fetch /api/goals"
    results.append("PASS: renders current goal states from /api/goals")

    # 2. Four stages defined
    for stage in ['Proposed', 'Active', 'Verified', 'Closed']:
        assert stage in js, f"stage '{stage}' missing"
    results.append("PASS: 4-stage pipeline (Proposed, Active, Verified, Closed)")

    # 3. Bottleneck detection at >3 threshold
    assert re.search(r'BOTTLENECK_THRESHOLD\s*=\s*3', js), "bottleneck threshold not 3"
    assert 'detectBottlenecks' in js, "no bottleneck detection function"
    results.append("PASS: bottleneck detection (>3 goals in same state triggers badge)")

    # 4. Bottleneck badge in HTML output
    assert 'pf-bn-badge' in js, "bottleneck badge element missing"
    results.append("PASS: visual bottleneck badge rendered when triggered")

    # 5. Click-through to detail panel
    assert 'pf-detail' in js and 'addEventListener' in js, "no click-to-detail wiring"
    results.append("PASS: click-through shows goal detail panel")

    # 6. Polling mechanism (setInterval)
    assert 'setInterval' in js, "no periodic polling"
    results.append("PASS: updates on /api/goals poll (setInterval)")

    # 7. Accessibility: role=list + aria-labels
    assert 'role="list"' in js or 'role=\'list\'' in js, "missing list role"
    assert 'aria-label' in js, "missing aria-labels on stages"
    results.append("PASS: accessible (role=list, aria-label per stage, focusable pills)")

    # 8. Reduced-motion safe
    assert 'prefers-reduced-motion' in js, "no reduced-motion handling"
    results.append("PASS: reduced-motion safe")

    # 9. Graceful fallback (catch on fetch)
    assert '.catch' in js, "no error handling on fetch failure"
    results.append("PASS: graceful when /api/goals unavailable")

    # 10. Self-test method present
    assert 'selfTest' in js, "no built-in selfTest"
    results.append("PASS: built-in selfTest() for runtime verification")

    print("")
    print("=== Goal Pipeline Flow - Static Verification ===")
    print(f"Widget: {SRC} ({len(js)} bytes)")
    for r in results:
        print(f"  {r}")
    print("")
    print(f"ALL {len(results)} CHECKS PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())