"""Wiring regression guard for Goal #4 (Fleet Status API Hardening) - 2026-11-22.

The CircuitBreaker module + its unit test (test_fleet_circuit_breaker.py) are solid,
but the goal was once marked 'wired into _fleet_snapshot()' when agent_portal.py did
NOT actually import/consult it (a mirror revert left the live endpoint with only the
15s negative cache). This guard FAILS if that wiring is ever removed again, so the
'claimed wired == actually wired' drift cannot silently reappear.

Runs 100% locally: reads agent_portal.py as SOURCE (no import -> no :8099 bind) and
drives the REAL CircuitBreaker module. No network / no egress needed from a sandbox.
Run:  python memory/mechanic/test_fleet_cb_wiring.py   (exit 0 = wired & consistent)
"""
import os
import re
import sys

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


def main():
    portal = os.path.join(_ROOT, "agent_portal.py")
    src = open(portal, encoding="utf-8").read()

    # --- (A) the breaker is actually imported + instantiated in the portal ---
    check("portal imports CircuitBreaker",
          re.search(r"from\s+fleet_circuit_breaker\s+import\s+CircuitBreaker", src) is not None)
    check("portal instantiates a shared breaker (_FLEET_CB)",
          re.search(r"_FLEET_CB\s*=\s*_?FleetCB\(|_FLEET_CB\s*=\s*CircuitBreaker\(", src) is not None)

    # --- (B) _fleet_snapshot actually consults it (skip-when-open + record outcomes) ---
    check("probe skips while circuit open (_FLEET_CB.is_open in probe path)",
          re.search(r"_FLEET_CB\.is_open\(b\)", src) is not None)
    check("probe records success to breaker", re.search(r"_FLEET_CB\.record_success\(b\)", src) is not None)
    check("probe records failure to breaker", re.search(r"_FLEET_CB\.record_failure\(b\)", src) is not None)

    # --- (C) the row rule emits an explicit DOWN state when open ---
    check('row sets state="down" on circuit-open', re.search(r'row\["state"\]\s*=\s*"down"', src) is not None)
    check("row reason carries 'circuit-open'", "circuit-open" in src)

    # --- (D) portal CB constants match the module defaults (no silent drift) ---
    m_strikes = re.search(r"FLEET_CB_STRIKES\s*=\s*(\d+)", src)
    m_cooldown = re.search(r"FLEET_CB_COOLDOWN\s*=\s*([0-9.]+)", src)
    check("FLEET_CB_STRIKES defined in portal", m_strikes is not None)
    check("FLEET_CB_COOLDOWN defined in portal", m_cooldown is not None)
    if m_strikes and m_cooldown:
        check("strikes == 3 (matches module default)", int(m_strikes.group(1)) == CircuitBreaker().strikes)
        check("cooldown == 60.0 (matches module default)", float(m_cooldown.group(1)) == CircuitBreaker().cooldown)

    # --- (E) the exact portal wiring sequence, driven on the REAL breaker ---
    cb = CircuitBreaker(strikes=3, cooldown=60.0)
    t0 = 1000.0
    ttl = 15.0  # FLEET_TTL: negative cache -> one strike per window for a dead host
    for _ in range(2):
        cb.record_failure("dead-host", t0); t0 += ttl + 1   # strikes 1,2 -> still closed
    check("wiring: dead host NOT down after 2 strikes", not cb.is_open("dead-host", t0))
    cb.record_failure("dead-host", t0)                       # strike 3 -> open
    check("wiring: dead host IS down after 3 consecutive failures", cb.is_open("dead-host", t0 + 1))
    check("wiring: down row would carry cooldown > 0", cb.cooldown_remaining("dead-host", t0 + 1) > 50)
    # a healthy host probed in the same window is unaffected (graceful degradation)
    cb.record_success("live-host")
    check("wiring: live host independent (not down)", not cb.is_open("live-host", t0))
    # after cooldown the dead host re-arms closed and needs fresh strikes
    t1 = t0 + 61.0
    check("wiring: breaker re-armed closed after cooldown", not cb.is_open("dead-host", t1))

    print(f"\nRESULT: {PASS} passed, {FAIL} failed")
    if FAIL:
        sys.exit(1)


if __name__ == "__main__":
    main()
