"""Integration test for Mechanic goal #4 (Fleet Status API Hardening) - proves the
REAL /api/fleet body path degrades gracefully, fully offline (no egress needed).

It imports agent_portal WITHOUT starting the server (serve_forever is under __main__),
monkeypatches _fleet_probe so no real network call happens, drives one host through
3 failed snapshots to trip its circuit breaker, then asserts the actual _fleet_snapshot()
dict returns that host as state='down' while every other host is still reported.
This is the offline stand-in for "simulated host-down returns 200 with that host marked
DOWN; other hosts still reported correctly."

Run:  python memory/mechanic/test_fleet_snapshot_integration.py   (exit 0 = pass)
"""
import os
import socket
import sys

socket.setdefaulttimeout(5)   # never hang on any stray I/O during import
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

try:
    import agent_portal as ap  # noqa: E402  (import only; server NOT started)
except Exception as e:  # pragma: no cover
    print("SKIP: could not import agent_portal offline (%r) - unit test still valid" % (e,))
    sys.exit(2)

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
    print("fleet snapshot integration test (offline, monkeypatched _fleet_probe)")

    # Choose a live host = local STUDIO; every other base in the fleet picture fails.
    live_base = ap.STUDIO.rstrip("/")

    def fake_probe(base, api_key="", timeout=3):
        return {"generations": 0, "models": []} if base.rstrip("/") == live_base else None

    orig_probe = ap._fleet_probe
    orig_ttl = ap.FLEET_TTL
    ap._fleet_probe = fake_probe
    ap.FLEET_TTL = 0          # no dead-cache suppression -> re-probe every snapshot in-test
    ap._fleet_breaker = __import__("fleet_circuit_breaker").CircuitBreaker(
        strikes=ap.FLEET_CB_STRIKES, cooldown=ap.FLEET_CB_COOLDOWN)
    try:
        snapshots = []
        down_seen_host = None
        for _ in range(ap.FLEET_CB_STRIKES + 1):
            snap = ap._fleet_snapshot()          # builds the real /api/fleet body
            snapshots.append(snap)
            rows = {r["base"].rstrip("/"): r for r in snap["hosts"]}
            live_row = rows.get(live_base)
            check("live host always reported idle (graceful degradation)",
                  live_row is not None and live_row["state"] == "idle")
            # first snapshot where any non-live host flips to 'down'
            for base, r in rows.items():
                if base != live_base and r["state"] == "down":
                    down_seen_host = (base, r)
        check("response shape has ts + ttl + hosts list",
              all(k in snapshots[-1] for k in ("ts", "ttl", "hosts")))
        check("a host-down is marked state='down' after 3 strikes",
              down_seen_host is not None)
        if down_seen_host:
            base, r = down_seen_host
            check("down row carries a circuit-open reason",
                  "circuit-open" in r.get("reason", "") and "cooldown" in r.get("reason", ""))
            others = [x for x in snapshots[-1]["hosts"] if x["base"].rstrip("/") != base]
            check("other hosts still present in the same response (partial data, no 500)",
                  len(others) >= 1 and any(x["state"] in ("idle", "busy") for x in others))
    finally:
        ap._fleet_probe = orig_probe
        ap.FLEET_TTL = orig_ttl

    print("\nRESULT: %d passed, %d failed" % (PASS, FAIL))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
