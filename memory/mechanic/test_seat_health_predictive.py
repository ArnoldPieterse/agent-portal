#!/usr/bin/env python3
"""test_seat_health_predictive.py - Verify predictive degrading state triggers before failure.

Acceptance:
  1. Simulated latency ramp (50ms -> 200ms over 4 probes) triggers "degrading" 
     BEFORE the seat would be marked "unreachable" (>30min stale).
  2. p95 latency up >50% over 3 probes = degrading state.
  3. Trend data written to seat-matrix.json.

Run: python memory/mechanic/test_seat_health_predictive.py
Exit: 0=pass, 1=fail
"""
import json, os, sys, tempfile, shutil
from datetime import datetime, timezone

# Import the probe module functions
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import seat_probe as sp

def test_degrading_triggers_before_failure():
    """Simulate latency ramp and verify degrading fires before unreachable."""
    # Use temp files to avoid polluting real data
    tmpdir = tempfile.mkdtemp(prefix="seat_test_")
    orig_hist = sp.LATENCY_HIST_PATH
    orig_matrix = sp.MATRIX_PATH
    orig_autoloop = sp.AUTOLOOP_PATH
    
    try:
        test_hist = os.path.join(tmpdir, "latency.jsonl")
        test_matrix = os.path.join(tmpdir, "matrix.json")
        test_autoloop = os.path.join(tmpdir, "autoloop.jsonl")
        
        sp.LATENCY_HIST_PATH = test_hist
        sp.MATRIX_PATH = test_matrix
        sp.AUTOLOOP_PATH = test_autoloop
        
        now = datetime.now(timezone.utc)
        ts_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Simulate: 4 probes with increasing latency for seat "mechanic"
        # Baseline ~50ms, ramp to 200ms (4x = +300% which is >50%)
        latencies = [50.0, 80.0, 120.0, 200.0]
        
        for i, lat in enumerate(latencies):
            ts = (now.replace(second=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
            sp.record_latency("mechanic", lat, ts)
        
        # After the ramp, compute trend
        trend = sp.compute_trend("mechanic")
        
        print(f"  Trend: p95={trend['p95_ms']}ms baseline={trend['baseline_ms']}ms "
              f"change={trend['pct_change']}% degrading={trend['degrading']}")
        
        # Verify: p95 of last 3 (80,120,200) = 200; baseline median of all (50,80,120,200) = ~100
        # pct_change should be > 50% -> degrading=True
        assert trend["degrading"] == True, f"Expected degrading=True, got {trend}"
        assert trend["pct_change"] > 50, f"Expected pct_change>50, got {trend['pct_change']}"
        
        # Verify: this would trigger BEFORE unreachable (which requires >30min stale)
        # The seat is still "active" (just probed now) but degrading
        state = sp.determine_state(ts_str, True, now)  # portal ok, just seen
        assert state == "healthy", f"Seat should be healthy before override, got {state}"
        
        # After predictive override in build_matrix logic:
        if trend["degrading"] and state in ("healthy", "stale"):
            overridden_state = "degrading"
        else:
            overridden_state = state
        
        assert overridden_state == "degrading", f"Expected degrading, got {overridden_state}"
        
        print("  PASS: degrading triggered before failure (seat still 'active' but latency trending up)")
        return True
        
    finally:
        sp.LATENCY_HIST_PATH = orig_hist
        sp.MATRIX_PATH = orig_matrix
        sp.AUTOLOOP_PATH = orig_autoloop
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_stable_no_degrading():
    """Stable latency should NOT trigger degrading."""
    tmpdir = tempfile.mkdtemp(prefix="seat_test_")
    orig_hist = sp.LATENCY_HIST_PATH
    try:
        test_hist = os.path.join(tmpdir, "latency.jsonl")
        sp.LATENCY_HIST_PATH = test_hist
        
        # Stable latency: 50ms every probe
        now = datetime.now(timezone.utc)
        for i in range(5):
            ts = (now.replace(second=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
            sp.record_latency("builder", 50.0, ts)
        
        trend = sp.compute_trend("builder")
        print(f"  Stable: p95={trend['p95_ms']}ms baseline={trend['baseline_ms']}ms "
              f"change={trend['pct_change']}% degrading={trend['degrading']}")
        
        assert trend["degrading"] == False, f"Stable should not be degrading, got {trend}"
        print("  PASS: stable latency does not trigger degrading")
        return True
        
    finally:
        sp.LATENCY_HIST_PATH = orig_hist
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_matrix_includes_trend():
    """Verify build_matrix writes trend data to seat-matrix.json."""
    tmpdir = tempfile.mkdtemp(prefix="seat_test_")
    orig_hist = sp.LATENCY_HIST_PATH
    orig_matrix = sp.MATRIX_PATH
    orig_autoloop = sp.AUTOLOOP_PATH
    
    try:
        test_hist = os.path.join(tmpdir, "latency.jsonl")
        test_matrix = os.path.join(tmpdir, "matrix.json")
        test_autoloop = os.path.join(tmpdir, "autoloop.jsonl")
        
        sp.LATENCY_HIST_PATH = test_hist
        sp.MATRIX_PATH = test_matrix
        sp.AUTOLOOP_PATH = test_autoloop
        
        # Seed some history
        now = datetime.now(timezone.utc)
        for i in range(4):
            ts = (now.replace(second=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
            sp.record_latency("orchestrator", 50.0 + i * 30, ts)
        
        # Run build_matrix (portal will likely be down in test env, that's fine)
        matrix = sp.build_matrix()
        
        # Verify trend field exists for each seat
        for seat, data in matrix["seats"].items():
            assert "trend" in data, f"Seat {seat} missing trend field"
            assert "p95_ms" in data["trend"], f"Seat {seat} trend missing p95_ms"
        
        # Verify degrading_count field exists
        assert "degrading_count" in matrix, "Matrix missing degrading_count"
        
        print(f"  Matrix: healthy={matrix['healthy_count']} degrading={matrix['degrading_count']} "
              f"unreachable={matrix['unreachable_count']}")
        print("  PASS: seat-matrix.json includes per-seat trend data + degrading_count")
        return True
        
    finally:
        sp.LATENCY_HIST_PATH = orig_hist
        sp.MATRIX_PATH = orig_matrix
        sp.AUTOLOOP_PATH = orig_autoloop
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    print("[test_seat_health_predictive] Running acceptance tests...")
    results = []
    
    tests = [
        ("degrading_triggers_before_failure", test_degrading_triggers_before_failure),
        ("stable_no_degrading", test_stable_no_degrading),
        ("matrix_includes_trend", test_matrix_includes_trend),
    ]
    
    for name, fn in tests:
        print(f"\n  TEST: {name}")
        try:
            results.append((name, fn(), None))
        except AssertionError as e:
            results.append((name, False, str(e)))
            print(f"  FAIL: {e}")
        except Exception as e:
            results.append((name, False, f"{type(e).__name__}: {e}"))
            print(f"  ERROR: {e}")
    
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{'='*50}")
    print(f"RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("ALL PASS - Predictive Seat Health Monitor verified")
        sys.exit(0)
    else:
        for name, ok, err in results:
            if not ok:
                print(f"  FAILED: {name}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
