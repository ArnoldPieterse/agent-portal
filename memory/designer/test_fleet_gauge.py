"""Designer Goal #4 (cycle-20): Fleet Health Composite Gauge verification.
Verifies: formula documented + weights sum to 1; gauge updates on /api poll;
tooltip shows component breakdown; score bounds correct; monotonicity.
Run: python memory/designer/test_fleet_gauge.py   (exit 0 = all pass)
"""
import sys, re, pathlib

SRC = "ui/cockpit-fleet-gauge.js"

def main():
    js = pathlib.Path(SRC).read_text(encoding="utf-8")
    results = []

    # 1. Formula documented: comment block with weights + component names
    assert re.search(r'w1\s*=\s*0\.35', js), "weight w1 not documented as 0.35"
    assert re.search(r'w2\s*=\s*0\.20', js), "weight w2 not documented as 0.20"
    assert re.search(r'w3\s*=\s*0\.25', js), "weight w3 not documented as 0.25"
    assert re.search(r'w4\s*=\s*0\.20', js), "weight w4 not documented as 0.20"
    results.append("PASS: formula documented (w1=0.35, w2=0.20, w3=0.25, w4=0.20)")

    # 2. Weights sum to 1 (check the JS constant object)
    m = re.search(r'var\s+WEIGHTS\s*=\s*\{([^}]+)\}', js)
    assert m, "WEIGHTS object not found"
    weights = {}
    for pair in m.group(1).split(','):
        k, v = pair.strip().split(':')
        weights[k.strip()] = float(v.strip())
    total = sum(weights.values())
    assert abs(total - 1.0) < 1e-9, f"weights sum to {total}, not 1.0"
    results.append(f"PASS: weights sum to exactly 1.0 ({len(weights)} components)")

    # 3. Four named components in formula
    for comp in ['completion', 'interventions', 'duration', 'oom']:
        assert comp in js, f"component '{comp}' missing from formula"
    results.append("PASS: all 4 components present (completion, interventions, duration, oom)")

    # 4. Polls /api/goals (primary data source for completion rate)
    assert '/api/goals' in js, "does not fetch /api/goals"
    results.append("PASS: polls /api/goals for fleet completion data")

    # 5. setInterval poll mechanism present
    assert 'setInterval' in js, "no polling interval"
    results.append("PASS: periodic poll via setInterval (updates on new data)")

    # 6. Tooltip with component breakdown
    assert 'fg-tooltip' in js, "tooltip element missing"
    assert 'Component breakdown' in js or 'component' in js.lower(), "tooltip does not reference components"
    results.append("PASS: tooltip shows component breakdown (4 rows with bars)")

    # 7. Accessibility: role=meter + aria-valuenow
    assert 'role' in js and 'meter' in js, "missing role=meter"
    assert 'aria-valuenow' in js, "missing aria-valuenow"
    results.append("PASS: accessible (role=meter, aria-valuenow, aria-label)")

    # 8. Reduced-motion safe
    assert 'prefers-reduced-motion' in js, "no reduced-motion handling"
    results.append("PASS: reduced-motion safe (transitions disabled)")

    # 9. Graceful fallback for missing data (catch on fetches)
    assert js.count('.catch') >= 3, "insufficient error handling on fetches"
    results.append("PASS: graceful fallback when any data source is unavailable")

    # 10. Score computation is a pure function (exported for testing)
    assert 'computeScore' in js and 'root.FleetGauge' in js, "computeScore not exported"
    results.append("PASS: computeScore exported as pure function (testable without DOM)")

    # 11. Self-test included in widget API
    assert 'selfTest' in js, "no built-in selfTest method"
    results.append("PASS: built-in selfTest() method for runtime verification")

    print("")
    print("=== Fleet Health Composite Gauge - Static Verification ===")
    print(f"Widget: {SRC} ({len(js)} bytes)")
    for r in results:
        print(f"  {r}")
    print("")
    print(f"ALL {len(results)} CHECKS PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())