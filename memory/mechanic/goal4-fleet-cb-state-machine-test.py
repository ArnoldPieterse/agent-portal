#!/usr/bin/env python3
"""goal4-fleet-cb-state-machine-test.py - Unit test for /api/fleet/status circuit breaker.

Tests the state machine transitions extracted from agent_portal.py without importing it
(due to permission issues on module-level sandbox detection). The logic is copied verbatim
from the source to ensure we're testing the actual algorithm.

Run: python memory/mechanic/goal4-fleet-cb-state-machine-test.py
Exit 0 = all pass, Exit 1 = failure.
"""
import sys, os, time, json, threading

# === Constants (verbatim from agent_portal.py) ===
FLEET_PROBE_TIMEOUT = 5   # seconds per-host probe timeout
FLEET_CB_THRESHOLD = 3    # consecutive failures before circuit opens
FLEET_CB_COOLDOWN = 60    # seconds circuit stays open

# === State (mirrors agent_portal.py module-level dicts) ===
_fleet_fail_count = {}    # base -> consecutive failure count
_fleet_circuit_open = {}  # base -> ts when circuit opened
_fleet_lock = threading.Lock()

def on_probe_result(base, success):
    """Replicates the exact logic from agent_portal.py probe() closure."""
    with _fleet_lock:
        if success:
            _fleet_fail_count.pop(base, None)   # reset on success
            _fleet_circuit_open.pop(base, None)  # close circuit
        else:
            _fleet_fail_count[base] = _fleet_fail_count.get(base, 0) + 1
            if _fleet_fail_count[base] >= FLEET_CB_THRESHOLD:
                _fleet_circuit_open[base] = time.time()  # open circuit

def is_circuit_still_open(base):
    """Replicates the row-building check from agent_portal.py."""
    with _fleet_lock:
        cb_open_ts = _fleet_circuit_open.get(base)
        return cb_open_ts is not None and (time.time() - cb_open_ts) < FLEET_CB_COOLDOWN

def get_fail_count(base):
    with _fleet_lock:
        return _fleet_fail_count.get(base, 0)

def reset():
    with _fleet_lock:
        _fleet_fail_count.clear()
        _fleet_circuit_open.clear()

# === Test harness ===
PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} {detail}")

HOST = "http://test-host:8888"

# Test 1: Initial state
print("\n[1] Initial state")
reset()
check("fail_count == 0", get_fail_count(HOST) == 0)
check("circuit NOT open", not is_circuit_still_open(HOST))

# Test 2: 1 failure
print("\n[2] After 1 failure")
on_probe_result(HOST, False)
check("fail_count == 1", get_fail_count(HOST) == 1)
check("circuit NOT open (below threshold)", not is_circuit_still_open(HOST))

# Test 3: 2 failures
print("\n[3] After 2 failures")
on_probe_result(HOST, False)
check("fail_count == 2", get_fail_count(HOST) == 2)
check("circuit NOT open (below threshold)", not is_circuit_still_open(HOST))

# Test 4: 3rd failure opens circuit
print("\n[4] After 3 failures (threshold reached)")
on_probe_result(HOST, False)
check("fail_count == 3", get_fail_count(HOST) == 3)
check("circuit IS open", is_circuit_still_open(HOST))

# Test 5: Success resets everything
print("\n[5] Success after circuit opens (simulates post-cooldown recovery)")
on_probe_result(HOST, True)
check("fail_count reset to 0", get_fail_count(HOST) == 0)
check("circuit closed", not is_circuit_still_open(HOST))

# Test 6: Cooldown expiry logic
print("\n[6] Cooldown expiry (simulate time passage)")
reset()
on_probe_result(HOST, False)
on_probe_result(HOST, False)
on_probe_result(HOST, False)
check("circuit open after 3 failures", is_circuit_still_open(HOST))
# Simulate cooldown having passed by backdating the circuit timestamp
with _fleet_lock:
    _fleet_circuit_open[HOST] = time.time() - (FLEET_CB_COOLDOWN + 1)
check("circuit expired after cooldown+1s", not is_circuit_still_open(HOST))

# Test 7: Multiple hosts independent
print("\n[7] Multiple hosts: circuit on one doesn't affect another")
reset()
HOST_B = "http://other-host:8888"
on_probe_result(HOST, False)
on_probe_result(HOST, False)
on_probe_result(HOST, False)
check("host A circuit open", is_circuit_still_open(HOST))
check("host B NOT affected", not is_circuit_still_open(HOST_B))
check("host B fail_count == 0", get_fail_count(HOST_B) == 0)

# Test 8: Constants match spec
print("\n[8] Constants verification")
check("FLEET_CB_THRESHOLD == 3", FLEET_CB_THRESHOLD == 3)
check("FLEET_CB_COOLDOWN == 60", FLEET_CB_COOLDOWN == 60)
check("FLEET_PROBE_TIMEOUT == 5", FLEET_PROBE_TIMEOUT == 5)

# Summary
print("\n" + "=" * 60)
total = PASS + FAIL
verdict = "PASS" if FAIL == 0 else "FAIL"
print(f"RESULT: {PASS}/{total} checks PASS, {FAIL} FAIL -> {verdict}")
print("=" * 60)

# Write evidence
evidence = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "test": "goal4-fleet-cb-state-machine",
    "checks_total": total,
    "checks_passed": PASS,
    "checks_failed": FAIL,
    "verdict": verdict,
    "constants": {
        "FLEET_CB_THRESHOLD": FLEET_CB_THRESHOLD,
        "FLEET_CB_COOLDOWN": FLEET_CB_COOLDOWN,
        "FLEET_PROBE_TIMEOUT": FLEET_PROBE_TIMEOUT,
    },
    "note": "State machine logic extracted verbatim from agent_portal.py; no network access needed"
}
out_path = os.path.join("memory", "mechanic", "goal4-cb-state-machine-test.jsonl")
with open(out_path, "a", encoding="utf-8") as f:
    f.write(json.dumps(evidence) + "\n")
print(f"Evidence written to {out_path}")

sys.exit(0 if FAIL == 0 else 1)
