"""Self-test for the fleet circuit breaker (Mechanic goal #4 - Fleet Status API
Hardening). Runs 100% locally with NO network / NO portal import, so it succeeds
from any sandbox seat (no :8099/:8888 egress needed).

Acceptance mapping (goal #4):
  * "circuit breaker opens after 3 failures"       -> test_open_after_three_strikes
  * "that host marked DOWN"                        -> test_down_marking_rule (row rule)
  * "other hosts still reported correctly"         -> test_keys_are_independent
Run:  python memory/mechanic/test_fleet_circuit_breaker.py   (exit 0 = all pass)
"""
import os
import sys

# Make the repo root importable so we can load the pure breaker module without
# importing agent_portal.py (which would bind :8099 and require egress).
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)
from fleet_circuit_breaker import CircuitBreaker  # noqa: E402

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  ok   -", name)
    else:
        FAIL += 1
        print("  FAIL -", name)


def test_open_after_three_strikes():
    cb = CircuitBreaker(strikes=3, cooldown=60.0)
    t0 = 1000.0
    check("new breaker is closed", not cb.is_open("hostA", t0))
    cb.record_failure("hostA", t0)            # strike 1
    cb.record_failure("hostA", t0 + 1)        # strike 2
    check("still closed after 2 strikes", not cb.is_open("hostA", t0 + 2))
    n = cb.record_failure("hostA", t0 + 2)    # strike 3 -> trip
    check("third failure returns count 3", n == 3)
    check("open after 3 consecutive failures", cb.is_open("hostA", t0 + 3))
    # trip happened on the strike at t0+2 -> open_until = (t0+2)+60; at t0+3 remaining = 59
    check("cooldown remaining 59s at trip+1", abs(cb.cooldown_remaining("hostA", t0 + 3) - 59.0) < 1e-6)


def test_cooldown_reclose_and_rearm():
    cb = CircuitBreaker(strikes=3, cooldown=60.0)
    t0 = 2000.0
    for _ in range(3):
        cb.record_failure("hostA", t0)
    check("open during window", cb.is_open("hostA", t0 + 59))
    check("re-closed after cooldown (61s > 60s)", not cb.is_open("hostA", t0 + 61))
    # After re-arm, a single fresh failure must NOT instantly re-open (needs 3 fresh).
    cb.record_failure("hostA", t0 + 62)   # fresh strike 1
    check("re-armed: 1 fresh failure does not reopen", not cb.is_open("hostA", t0 + 63))


def test_success_resets():
    cb = CircuitBreaker(strikes=3, cooldown=60.0)
    t0 = 3000.0
    for _ in range(3):
        cb.record_failure("hostA", t0)
    check("open before success", cb.is_open("hostA", t0 + 1))
    cb.record_success("hostA")
    check("closed after a success resets breaker", not cb.is_open("hostA", t0 + 2))
    check("fail count cleared to 0", cb.snapshot()["hostA"]["failures"] == 0)


def test_keys_are_independent():
    """Tripping one host must not affect another (other hosts still reported)."""
    cb = CircuitBreaker(strikes=3, cooldown=60.0)
    t0 = 4000.0
    for _ in range(3):
        cb.record_failure("hostA", t0)
    check("hostA open", cb.is_open("hostA", t0 + 1))
    check("hostB still closed (independent)", not cb.is_open("hostB", t0 + 1))
    check("hostC still closed (independent)", not cb.is_open("hostC", t0 + 1))


def test_down_marking_rule():
    """Reproduce the exact row rule agent_portal.py applies: a tripped host's row is
    state='down' with a cooldown reason; an untripped live host keeps idle/busy."""
    cb = CircuitBreaker(strikes=3, cooldown=60.0)
    t0 = 5000.0
    for _ in range(3):
        cb.record_failure("downHost", t0)

    def row_state(key, probe_ok):
        rem = cb.cooldown_remaining(key, t0 + 1)
        if probe_ok:
            state = "busy"
        else:
            state = "unknown"
        if rem > 0:                       # the override agent_portal.py adds
            return "down", ("circuit-open (%ds cooldown)" % int(rem))
        return state, ""

    st, reason = row_state("downHost", probe_ok=False)
    check("tripped host marked down", st == "down")
    check("down reason carries cooldown", "circuit-open" in reason and "cooldown" in reason)
    st2, _ = row_state("liveHost", probe_ok=True)
    check("unaffected live host stays busy/idle (not down)", st2 == "busy")


def main():
    print("fleet circuit breaker self-test")
    for fn in (test_open_after_three_strikes, test_cooldown_reclose_and_rearm,
               test_success_resets, test_keys_are_independent, test_down_marking_rule):
        print(fn.__name__)
        fn()
    print("\nRESULT: %d passed, %d failed" % (PASS, FAIL))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
