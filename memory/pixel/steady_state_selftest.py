#!/usr/bin/env python3
"""
Sandbox-runnable self-test for the cockpit steady-state decision logic.

Mirrors ui/uploads.js `_applyFleetState(o)` (L514-527) EXACTLY, as a pure
Python port of the same expressions, so the convergence state machine can be
gated WITHOUT a browser / non-sandbox seat. This covers the DECISION LOGIC leg
only; it does NOT cover DOM render or Playwright console-error checks (those
still require a live browser seat).

Decision table (from uploads.js):
    guard:  not o or not o.ok            -> no-op (state unchanged)
    c1     = (o.fleet_pct or 0) >= 100
    c2     = all((a.open or 0)==0 for a in (o.agents or []))   # vacuously True on empty list
    state  = steady if c1 and c2 else converging if (c1 or c2) else active
    partial bar text (converging only):
        c1 true  -> "Converging… steady-state pending"
        c1 false -> "Converging… <pct>% goals · convergence pending"

Exit: 0 = ALL PASS, 1 = FAIL.
"""
import sys


def apply_fleet_state(o):
    """Faithful port of _applyFleetState. Returns (state, partial_text) or None on guard."""
    if not o or not o.get("ok"):
        return None  # no-op: body.dataset.fleetState unchanged
    c1 = (o.get("fleet_pct") or 0) >= 100
    agents = o.get("agents") or []
    c2 = all((a.get("open") or 0) == 0 for a in agents)
    state = "steady" if (c1 and c2) else ("converging" if (c1 or c2) else "active")
    partial = None
    if state == "converging":
        pct = "steady-state pending" if c1 else f"{(o.get('fleet_pct') or 0)}% goals · convergence pending"
        partial = "Converging… " + pct
    return state, partial


cases = [
    # (label, payload, expected_state, expected_partial)
    ("guard: None payload -> no-op",        None,                                   None,  None),
    ("guard: ok=false -> no-op",            {"ok": False, "fleet_pct": 100},         None,  None),
    ("steady: 100% + all closed",           {"ok": True, "fleet_pct": 100, "agents": [{"open": 0}, {"open": 0}]}, "steady",     None),
    ("steady boundary: pct exactly 100",    {"ok": True, "fleet_pct": 100.0, "agents": []},                 "steady",     None),
    ("converging: 99.9% + all closed (c2 only)", {"ok": True, "fleet_pct": 99.9, "agents": [{"open": 0}]},   "converging", "Converging… 99.9% goals · convergence pending"),
    ("converging: 100% but one open (c1 only)", {"ok": True, "fleet_pct": 100, "agents": [{"open": 2}]},     "converging", "Converging… steady-state pending"),
    ("converging: 87% + all closed (c2 only)",   {"ok": True, "fleet_pct": 87, "agents": []},                "converging", "Converging… 87% goals · convergence pending"),
    ("active: 50% + one open (neither)",     {"ok": True, "fleet_pct": 50, "agents": [{"open": 3}]},        "active",     None),
    ("empty agents -> c2 vacuously true; pct<100 -> converging", {"ok": True, "fleet_pct": 42},             "converging", "Converging… 42% goals · convergence pending"),
    ("missing fleet_pct + missing agents -> active? no: c2 vacuous true -> converging", {"ok": True},        "converging", "Converging… 0% goals · convergence pending"),
    ("agents with null open treated as 0 -> closed", {"ok": True, "fleet_pct": 100, "agents": [{"open": None}]}, "steady", None),
]

fails = 0
for label, payload, want_state, want_partial in cases:
    res = apply_fleet_state(payload)
    if res is None:
        got_state, got_partial = None, None
    else:
        got_state, got_partial = res
    ok = (got_state == want_state) and (got_partial == want_partial)
    status = "PASS" if ok else "FAIL"
    if not ok:
        fails += 1
    print(f"[{status}] {label}")
    if not ok:
        print(f"       want=({want_state!r}, {want_partial!r})")
        print(f"       got =({got_state!r}, {got_partial!r})")

print(f"\nRESULT {'ALL PASS' if fails == 0 else f'{fails} FAILED'} ({len(cases) - fails}/{len(cases)})")
sys.exit(1 if fails else 0)
