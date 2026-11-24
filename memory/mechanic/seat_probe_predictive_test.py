#!/usr/bin/env python3
"""seat_probe_predictive_test.py - Verify Predictive Seat Health Monitor (Goal #1).

Acceptance criteria:
- Simulated latency ramp triggers "degrading" state BEFORE actual failure
- p95 > 1.5x baseline for 3 consecutive probes => degrading
- Trend data written to seat-matrix.json under each seat's latency_trend field
"""
import json, os, sys, subprocess, statistics
from datetime import datetime, timezone, timedelta

PROBE = 'memory/mechanic/seat_probe.py'
MATRIX = pathlib.Path('memory/ops/seat-matrix.json') if 'pathlib' in dir() else None
HISTORY = 'memory/ops/seat-latency-history.jsonl'
AUTOLOOP = 'memory/ops/autoloop.jsonl'

import pathlib
MATRIX_PATH = pathlib.Path('memory/ops/seat-matrix.json')
HISTORY_PATH = pathlib.Path('memory/ops/seat-latency-history.jsonl')
AUTOLOOP_PATH = pathlib.Path('memory/ops/autoloop.jsonl')

SEATS = ["orchestrator", "researcher", "builder", "verifier",
         "designer", "archivist", "scribe", "mechanic"]

def setup_healthy_autoloop():
    """Write autoloop entries showing all seats recently active."""
    now = datetime.now(timezone.utc)
    recent_ts = (now - timedelta(minutes=2)).isoformat()
    entries = [{"timestamp": recent_ts, "agent": s.capitalize(), "task_type": "WORK", "productive": True} for s in SEATS]
    AUTOLOOP_PATH.write_text('\n'.join(json.dumps(e) for e in entries) + '\n', encoding='utf-8')

def clear_history():
    """Remove latency history for clean test."""
    if HISTORY_PATH.exists():
        HISTORY_PATH.unlink()

def simulate_latency_ramp(seat, baseline_ms=50, ramp_factor=2.0, num_probes=6):
    """Simulate a latency ramp: start at baseline, increase to baseline*ramp_factor.
    
    Writes entries to the history file directly (bypassing live probe).
    Returns the final state from seat-matrix.json for that seat.
    """
    now = datetime.now(timezone.utc)
    
    # Phase 1: Normal readings (baseline)
    normal_readings = []
    for i in range(4):
        ts = (now - timedelta(minutes=(num_probes + 3 - i) * 5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        latency = baseline_ms + (i % 2) * 2  # slight variance
        normal_readings.append({"ts": ts, "seat": seat, "latency_ms": latency})
    
    # Phase 2: Ramp readings (increasing)
    ramp_readings = []
    for i in range(num_probes):
        ts = (now - timedelta(minutes=(num_probes - 1 - i) * 5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Linear ramp from baseline to baseline*ramp_factor
        progress = (i + 1) / num_probes
        latency = round(baseline_ms + (baseline_ms * (ramp_factor - 1)) * progress, 1)
        ramp_readings.append({"ts": ts, "seat": seat, "latency_ms": latency})
    
    # Write all to history file
    with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
        for entry in normal_readings + ramp_readings:
            f.write(json.dumps(entry) + '\n')
    
    return normal_readings + ramp_readings

def run_probe():
    """Run the probe and return (exit_code, stdout, matrix_dict)."""
    r = subprocess.run([sys.executable, PROBE], capture_output=True, text=True)
    matrix = json.loads(MATRIX_PATH.read_text(encoding='utf-8')) if MATRIX_PATH.exists() else {}
    return r.returncode, r.stdout.strip(), matrix

def test_degrading_before_failure():
    """Test: latency ramp triggers degrading BEFORE the seat goes fully unreachable."""
    print("=== TEST 1: Degrading state triggers before actual failure ===")
    
    setup_healthy_autoloop()
    clear_history()
    
    # Simulate a ramp for 'researcher' seat: baseline 50ms -> 120ms (2.4x)
    readings = simulate_latency_ramp('researcher', baseline_ms=50, ramp_factor=2.4, num_probes=6)
    
    # Run probe to process the history
    code, out, matrix = run_probe()
    
    researcher = matrix.get('seats', {}).get('researcher', {})
    state = researcher.get('state', 'unknown')
    trend = researcher.get('latency_trend', {})
    
    print(f"  State: {state}")
    print(f"  Trend: p95={trend.get('p95_ms')}ms baseline={trend.get('baseline_ms')}ms ratio={trend.get('ratio')}")
    print(f"  Degrading: {trend.get('degrading')}, consecutive_above={trend.get('consecutive_above')}")
    
    assert state == 'degrading', f"FAIL: expected 'degrading', got '{state}'"
    assert trend.get('degrading') == True, "FAIL: trend.degrading should be True"
    assert trend.get('ratio', 0) > 1.5, f"FAIL: ratio {trend.get('ratio')} should be > 1.5"
    print("  PASS: degrading detected before failure\n")

def test_healthy_stays_healthy():
    """Test: stable latency does NOT trigger degrading."""
    print("=== TEST 2: Stable latency remains healthy ===")
    
    setup_healthy_autoloop()
    clear_history()
    
    # Write stable readings (no ramp)
    now = datetime.now(timezone.utc)
    with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
        for i in range(10):
            ts = (now - timedelta(minutes=(10 - i) * 5)).strftime("%Y-%m-%dT%H:%M:%SZ")
            latency = 50 + (i % 3) * 2  # 50, 52, 54ms variance
            f.write(json.dumps({"ts": ts, "seat": "builder", "latency_ms": latency}) + '\n')
    
    code, out, matrix = run_probe()
    builder = matrix.get('seats', {}).get('builder', {})
    state = builder.get('state', 'unknown')
    trend = builder.get('latency_trend', {})
    
    print(f"  State: {state}")
    print(f"  Trend: p95={trend.get('p95_ms')}ms baseline={trend.get('baseline_ms')}ms ratio={trend.get('ratio')}")
    
    assert state == 'healthy', f"FAIL: expected 'healthy', got '{state}'"
    assert not trend.get('degrading'), "FAIL: should NOT be degrading with stable latency"
    print("  PASS: stable latency stays healthy\n")

def test_trend_data_in_matrix():
    """Test: seat-matrix.json contains latency_trend field with required keys."""
    print("=== TEST 3: Trend data written to seat-matrix.json ===")
    
    setup_healthy_autoloop()
    clear_history()
    simulate_latency_ramp('designer', baseline_ms=40, ramp_factor=2.0, num_probes=5)
    
    code, out, matrix = run_probe()
    designer = matrix.get('seats', {}).get('designer', {})
    trend = designer.get('latency_trend')
    
    assert trend is not None, "FAIL: latency_trend field missing from seat-matrix.json"
    required_keys = ['p95_ms', 'baseline_ms', 'ratio', 'degrading', 'consecutive_above', 'samples']
    for key in required_keys:
        assert key in trend, f"FAIL: missing key '{key}' in latency_trend"
    
    print(f"  All {len(required_keys)} required keys present: {list(trend.keys())}")
    print("  PASS: trend data complete in matrix\n")

def test_unreachable_still_works():
    """Test: original unreachable detection still functions."""
    print("=== TEST 4: Unreachable detection preserved ===")
    
    # Write autoloop with one old seat
    now = datetime.now(timezone.utc)
    recent_ts = (now - timedelta(minutes=2)).isoformat()
    old_ts = (now - timedelta(minutes=45)).isoformat()
    
    entries = [{"timestamp": recent_ts, "agent": s.capitalize(), "task_type": "WORK", "productive": True} for s in SEATS if s != 'archivist']
    entries.append({"timestamp": old_ts, "agent": "Archivist", "task_type": "WORK", "productive": True})
    AUTOLOOP_PATH.write_text('\n'.join(json.dumps(e) for e in entries) + '\n', encoding='utf-8')
    
    clear_history()
    code, out, matrix = run_probe()
    
    archivist = matrix.get('seats', {}).get('archivist', {})
    state = archivist.get('state', 'unknown')
    cascade = matrix.get('cascade', False)
    
    print(f"  Archivist state: {state}, cascade: {cascade}")
    assert state == 'unreachable', f"FAIL: expected 'unreachable', got '{state}'"
    assert cascade == True, "FAIL: cascade should be True"
    print("  PASS: unreachable detection works\n")

if __name__ == '__main__':
    # Save original autoloop
    orig_autoloop = AUTOLOOP_PATH.read_text(encoding='utf-8') if AUTOLOOP_PATH.exists() else ''
    
    try:
        test_degrading_before_failure()
        test_healthy_stays_healthy()
        test_trend_data_in_matrix()
        test_unreachable_still_works()
        print("=== ALL PREDICTIVE HEALTH TESTS PASSED ===")
    finally:
        # Restore original autoloop
        if orig_autoloop:
            AUTOLOOP_PATH.write_text(orig_autoloop, encoding='utf-8')
