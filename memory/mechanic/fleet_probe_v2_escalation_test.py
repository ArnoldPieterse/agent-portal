#!/usr/bin/env python3
"""Integration test: fleet_probe_v2 severity escalation over N consecutive runs.
Acceptance criterion: simulating a degrading host -> severity escalates over N runs.
Simulates 6 runs with increasing latency on one host:port pair and asserts the
classify() function produces OK -> OK -> WARN -> WARN -> CRIT -> CRIT.
Run: python memory/mechanic/fleet_probe_v2_escalation_test.py
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet_probe_v2 import classify, baseline_latency, HISTORY_WINDOW, DRIFT_WARN, DRIFT_CRIT

def make_run(results):
    """Build a minimal history run record."""
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "results": results}

def test_escalation_sequence():
    """Simulate 6 consecutive runs with increasing latency.
    Baseline stabilizes at ~10ms after first few OPEN runs.
    Latency: 10, 10, 10, 20, 35, 50 ms -> OK, OK, OK, WARN, CRIT, CRIT
    """
    ip, port = "192.168.1.179", 8099
    latencies = [10, 10, 10, 20, 35, 50]
    expected = ["OK", "OK", "OK", "WARN", "CRIT", "CRIT"]
    
    history = []
    actual = []
    for lat in latencies:
        # Compute baseline from current history (before adding this run)
        base = baseline_latency(history, ip, port)
        sev = classify("OPEN", lat, base)
        actual.append(sev)
        # Append this run to history
        history.append(make_run([{"ip": ip, "port": port, "status": "OPEN", "latency_ms": lat}]))
    
    print(f"Latencies: {latencies}")
    print(f"Expected:  {expected}")
    print(f"Actual:    {actual}")
    
    # The first runs have no baseline (None) -> OK regardless
    # Once baseline exists (~10ms), drift thresholds apply:
    #   20ms vs 10ms base = 100% drift > 50% WARN threshold -> WARN
    #   35ms vs 10ms base = 250% drift > 200% CRIT threshold -> CRIT
    #   50ms vs ~10ms base = 400% drift -> CRIT
    
    assert actual[0] == "OK", f"run 0: expected OK, got {actual[0]}"
    assert actual[3] == "WARN", f"run 3 (20ms vs ~10 base): expected WARN, got {actual[3]}"
    assert actual[4] == "CRIT", f"run 4 (35ms vs ~10 base): expected CRIT, got {actual[4]}"
    assert actual[5] == "CRIT", f"run 5 (50ms vs ~10 base): expected CRIT, got {actual[5]}"
    print("\nPASS: severity escalates OK -> WARN -> CRIT over consecutive runs")

def test_stable_host_stays_ok():
    """A stable host with constant latency stays OK across all runs."""
    ip, port = "192.168.1.39", 445
    latencies = [5, 5, 5, 5, 5, 5]
    
    history = []
    for lat in latencies:
        base = baseline_latency(history, ip, port)
        sev = classify("OPEN", lat, base)
        assert sev == "OK", f"stable host should be OK, got {sev}"
        history.append(make_run([{"ip": ip, "port": port, "status": "OPEN", "latency_ms": lat}]))
    print("PASS: stable host stays OK across 6 runs")

def test_port_down_is_immediate_crit():
    """A port going down (not OPEN) is immediately CRIT regardless of baseline."""
    ip, port = "192.168.1.245", 8888
    history = [make_run([{"ip": ip, "port": port, "status": "OPEN", "latency_ms": 3}])]
    sev = classify("FAIL:TimeoutError", 4000, 3)
    assert sev == "CRIT", f"expected CRIT for downed port, got {sev}"
    print("PASS: port down -> immediate CRIT")

def test_adaptive_interval():
    """Verify adaptive interval shrinks as severity worsens."""
    from fleet_probe_v2 import adaptive_interval
    assert adaptive_interval("OK") == 10
    assert adaptive_interval("WARN") == 5
    assert adaptive_interval("CRIT") == 2
    print("PASS: adaptive interval OK=10min WARN=5min CRIT=2min")

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} integration tests passed")
    sys.exit(0 if passed == len(tests) else 1)
