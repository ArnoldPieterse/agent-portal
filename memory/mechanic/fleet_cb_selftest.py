"""Self-test for Fleet Status API circuit breaker logic (Goal #4 hardening).
Tests the state machine without live network access by simulating probe outcomes."""
import sys, time, threading

# Simulate the circuit breaker state machine as implemented in agent_portal.py
FLEET_CB_THRESHOLD = 3
FLEET_CB_COOLDOWN = 60
FLEET_TTL = 15

_fleet_fail_count = {}
_fleet_circuit_open = {}
_fleet_dead = {}
_fleet_cache = {}
_lock = threading.Lock()

def simulate_probe(base, should_succeed, now):
    """Mimics the probe() inner function from _fleet_snapshot()."""
    with _lock:
        cached_dead = (now - _fleet_dead.get(base, 0)) < FLEET_TTL
        cb_open_ts = _fleet_circuit_open.get(base)
        cb_still_open = cb_open_ts is not None and (now - cb_open_ts) < FLEET_CB_COOLDOWN
    
    if cached_dead or cb_still_open:
        return None  # skip probe
    
    res = {"generations": 0, "models": []} if should_succeed else None
    
    with _lock:
        if res is not None:
            _fleet_cache[base] = now
            _fleet_dead.pop(base, None)
            _fleet_fail_count.pop(base, None)
            _fleet_circuit_open.pop(base, None)
        else:
            _fleet_dead[base] = now
            _fleet_fail_count[base] = _fleet_fail_count.get(base, 0) + 1
            if _fleet_fail_count[base] >= FLEET_CB_THRESHOLD:
                _fleet_circuit_open[base] = now
    return res

def get_state(base, now):
    """Mimics the row-building logic for state/reason."""
    with _lock:
        cb_open_ts = _fleet_circuit_open.get(base)
        cb_active = cb_open_ts is not None and (now - cb_open_ts) < FLEET_CB_COOLDOWN
    if cb_active:
        remaining = int(FLEET_CB_COOLDOWN - (now - cb_open_ts))
        return "down", "circuit-open (%ds remaining)" % remaining
    elif base in _fleet_dead:
        last_seen = _fleet_cache.get(base)
        reason = "unreachable" if last_seen is None else "stale (%ds)" % int(now - last_seen)
        return "unknown", reason
    return "idle", ""

# --- TESTS ---
passed = 0
failed = 0

def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}")

print("Circuit Breaker Self-Test")
print("=" * 50)

# Test 1: First two failures do NOT open circuit
t = 1000.0
simulate_probe("host-a", False, t)
state, reason = get_state("host-a", t)
check("T1a: 1st failure -> unknown/unreachable", state == "unknown" and "unreachable" in reason)

# Wait past FLEET_TTL to allow re-probe
t += FLEET_TTL + 1
simulate_probe("host-a", False, t)
state, reason = get_state("host-a", t)
check("T1b: 2nd failure -> still unknown (circuit NOT open)", state == "unknown")

# Test 2: Third consecutive failure OPENS circuit
t += FLEET_TTL + 1
simulate_probe("host-a", False, t)
state, reason = get_state("host-a", t)
check("T2a: 3rd failure -> circuit opens (state=down)", state == "down" and "circuit-open" in reason)

# Test 3: While circuit is open, probes are SKIPPED
t += 5  # only 5s into 60s cooldown
result = simulate_probe("host-a", True, t)  # would succeed but should be skipped
check("T3a: probe skipped while circuit open", result is None)
state, reason = get_state("host-a", t)
check("T3b: still down after skip", state == "down")

# Test 4: After cooldown expires, next success CLOSES circuit
t += FLEET_CB_COOLDOWN + 1  # past the 60s cooldown
result = simulate_probe("host-a", True, t)
check("T4a: probe allowed after cooldown", result is not None)
state, reason = get_state("host-a", t)
check("T4b: circuit closed on success (state=idle)", state == "idle")

# Test 5: Fresh host - no false positives
t += 100
state, reason = get_state("host-b", t)
check("T5a: fresh host -> idle", state == "idle")

# Test 6: Circuit opens for one host but not another
_fleet_fail_count.clear()
_fleet_circuit_open.clear()
_fleet_dead.clear()
_fleet_cache.clear()
t = 2000.0
for i in range(3):
    simulate_probe("host-x", False, t + i * (FLEET_TTL + 1))
simulate_probe("host-y", True, t)
state_x, _ = get_state("host-x", t + 3 * FLEET_TTL)
state_y, _ = get_state("host-y", t + 3 * FLEET_TTL)
check("T6a: host-x circuit open after 3 fails", state_x == "down")
check("T6b: host-y unaffected (idle)", state_y == "idle")

print(f"\nResults: {passed} PASS, {failed} FAIL / {passed+failed} total")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")
    sys.exit(1)
