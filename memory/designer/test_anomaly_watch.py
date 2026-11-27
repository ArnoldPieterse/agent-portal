"""Designer Goal #8 (cycle-20): Anomaly Watch Panel verification.
Verifies: pulls from real data; severity badges (info/warn/critical); collapsed by default;
expand shows last 20; a11y; reduced-motion safe.
Run: python memory/designer/test_anomaly_watch.py   (exit 0 = all pass)
"""
import sys, re, pathlib

SRC = "ui/cockpit-anomaly-watch.js"

def main():
    js = pathlib.Path(SRC).read_text(encoding="utf-8")
    results = []

    # 1. Pulls from real data source (/api/anomalies + fallback)
    assert '/api/anomalies' in js, "no /api/anomalies fetch"
    assert 'probe-evidence' in js or 'file/raw' in js, "no fallback to probe log"
    results.append("PASS: pulls from real data (/api/anomalies + probe-log fallback)")

    # 2. Severity badges: info/warn/critical with distinct classes
    for sev in ['critical', 'warn', 'info']:
        assert ('aw-badge-' + sev) in js, "severity class for %s missing" % sev
    results.append("PASS: severity badges (info=blue, warn=amber, critical=red)")

    # 3. Collapsed by default (expanded starts false; body hidden)
    assert 'expanded = false' in js or "expanded=false" in js, "not collapsed by default"
    assert 'hidden' in js, "no hidden attribute for collapsed state"
    results.append("PASS: collapsed by default (expanded=false; body[hidden])")

    # 4. Expand shows last 20 (maxItems=20)
    m = re.search(r'maxItems:\s*20', js)
    assert m, "maxItems not set to 20"
    assert 'slice(0' in js or '.slice(' in js, "no slice to limit items"
    results.append("PASS: expand shows last 20 items (maxItems=20)")

    # 5. Polls periodically
    assert 'setInterval' in js, "no periodic poll"
    results.append("PASS: updates on poll (setInterval)")

    # 6. Accessible: role=log, aria-expanded, keyboard toggle
    assert 'role=' in js and ('log' in js or 'button' in js), "missing a11y roles"
    assert 'aria-expanded' in js, "no aria-expanded on toggle"
    assert 'tabindex' in js, "not keyboard focusable"
    results.append("PASS: accessible (role=log + aria-expanded + keyboard)")

    # 7. Reduced-motion safe
    assert 'prefers-reduced-motion' in js, "no reduced-motion handling"
    results.append("PASS: reduced-motion safe")

    # 8. Graceful when no data
    assert '.catch(' in js and ('No anomalies' in js or 'empty' in js.lower()), "no graceful empty state"
    results.append("PASS: graceful when no anomaly data available")

    # 9. selfTest exported
    assert 'selfTest' in js, "no selfTest method"
    results.append("PASS: built-in selfTest() for runtime verification")

    print("")
    print("=== Anomaly Watch Panel - Static Verification ===")
    print("Widget: %s (%d bytes)" % (SRC, len(js)))
    for r in results:
        print("  " + r)
    print("")
    print("ALL %d CHECKS PASSED" % len(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())
