#!/usr/bin/env python3
"""Unit test for fleet_probe_v2.py process-count anomaly detection.
Simulates history with known baselines and asserts severity classification.
Run: python memory/mechanic/fleet_probe_v2_test.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet_probe_v2 import classify_proc, baseline_proc_count, PROC_SPIKE_WARN, PROC_SPIKE_CRIT

def test_baseline_median():
    history = [{"proc_count": v} for v in [100, 102, 98, 101, 99]]
    assert baseline_proc_count(history) == 100, f"expected 100, got {baseline_proc_count(history)}"
    print("PASS: baseline_proc_count median")

def test_baseline_empty():
    assert baseline_proc_count([]) is None
    print("PASS: baseline empty -> None")

def test_ok_no_drift():
    sev, drift = classify_proc(100, 100)
    assert sev == "OK" and drift == 0.0
    print(f"PASS: no drift -> OK (drift={drift})")

def test_warn_spike():
    # 35% spike > 30% WARN threshold
    sev, drift = classify_proc(135, 100)
    assert sev == "WARN", f"expected WARN, got {sev}"
    assert abs(drift - 0.35) < 0.01
    print(f"PASS: +35% spike -> WARN (drift={drift})")

def test_warn_drop():
    # 40% drop > 30% WARN threshold (absolute drift)
    sev, drift = classify_proc(60, 100)
    assert sev == "WARN", f"expected WARN, got {sev}"
    print(f"PASS: -40% drop -> WARN (drift={drift})")

def test_crit_spike():
    # 150% spike > 100% CRIT threshold
    sev, drift = classify_proc(250, 100)
    assert sev == "CRIT", f"expected CRIT, got {sev}"
    print(f"PASS: +150% spike -> CRIT (drift={drift})")

def test_crit_drop():
    # 120% drop > 100% CRIT threshold
    sev, drift = classify_proc(80, 40)  # baseline 40, count 80 -> +100%... let's use a real drop
    # Better: baseline 200, count 50 -> -75% which is WARN not CRIT
    # For CRIT drop: baseline 200, count 10 -> -95% > 100%? No, abs(10-200)/200 = 0.95 < 1.0
    # Need >100%: impossible for drops (max is 100%). So CRIT only fires on spikes.
    sev, drift = classify_proc(400, 100)  # +300%
    assert sev == "CRIT"
    print(f"PASS: +300% spike -> CRIT (drift={drift})")

def test_none_inputs():
    sev, drift = classify_proc(None, 100)
    assert sev == "OK" and drift is None
    sev, drift = classify_proc(100, None)
    assert sev == "OK" and drift is None
    sev, drift = classify_proc(0, 0)
    assert sev == "OK"
    print("PASS: None/zero inputs -> OK")

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1)
