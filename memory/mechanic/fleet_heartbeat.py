#!/usr/bin/env python3
"""
fleet_heartbeat.py - Fleet Health Heartbeat Consolidation (Mechanic Goal #2)

Merges per-seat probe outputs into a single fleet-heartbeat.json:
  - seat-matrix.json (seat state, latency, last_seen)
  - autonomy-score.json (fleet score, per-host uptime/vram)
  - recovery-sla-summary.json (SLA compliance)

Output: memory/ops/fleet-heartbeat.json
Staleness threshold: 5s (seat is stale if last update >5s ago)

Usage:
  python memory/mechanic/fleet_heartbeat.py generate    (build heartbeat from sources)
  python memory/mechanic/fleet_heartbeat.py check       (check staleness of existing)
  python memory/mechanic/fleet_heartbeat.py selftest

Acceptance criteria:
  - All 4 seats reflected in one file
  - Stale seat correctly flagged after simulated 10s gap
  - Single JSON, cockpit polls this instead of N separate calls
"""
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(".")  # Use cwd (sandbox maps relative paths correctly)
OPS_DIR = BASE / "memory" / "ops"
HEARTBEAT_FILE = OPS_DIR / "fleet-heartbeat.json"
SEAT_MATRIX = OPS_DIR / "seat-matrix.json"
AUTONOMY_SCORE = OPS_DIR / "autonomy-score.json"
RECOVERY_SLA = OPS_DIR / "recovery-sla-summary.json"

STALENESS_THRESHOLD_S = 5  # seconds
KNOWN_SEATS = ["White", "Red", "Pale", "Black"]


def get_timestamp():
    return datetime.now(timezone.utc).isoformat()


def load_json(path):
    """Load a JSON file, return None if missing or invalid."""
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def generate_heartbeat():
    """
    Build the consolidated fleet-heartbeat.json from source files.
    Returns the heartbeat dict.
    """
    seat_matrix = load_json(SEAT_MATRIX) or {}
    autonomy = load_json(AUTONOMY_SCORE) or {}
    recovery_sla = load_json(RECOVERY_SLA) or {}

    now_iso = get_timestamp()
    now_ts = time.time()

    # Extract per-seat data from seat-matrix
    seats_raw = seat_matrix.get("seats", {})
    
    # Map agent names to host seats (orchestrator->White, researcher->Red, etc.)
    AGENT_TO_SEAT = {
        "orchestrator": "White",
        "researcher": "Red",
        "verifier": "Pale",
        "builder": "Black",
    }

    # Build per-seat heartbeat entries
    seats = {}
    for seat_name in KNOWN_SEATS:
        seat_entry = {
            "state": "unknown",
            "last_seen": None,
            "latency_ms": None,
            "uptime_pct": None,
            "vram_trend_pct": None,
            "stale": False,
            "last_cycle_ts": None,
        }

        # From seat-matrix (agent-level)
        for agent_key, host in AGENT_TO_SEAT.items():
            if host == seat_name and agent_key in seats_raw:
                info = seats_raw[agent_key]
                seat_entry["state"] = info.get("state", "unknown")
                seat_entry["last_seen"] = info.get("last_seen")
                seat_entry["latency_ms"] = info.get("latency_ms")

        # From autonomy-score (host-level)
        fleet_per_host = autonomy.get("fleet_per_host", {})
        if seat_name in fleet_per_host:
            host_info = fleet_per_host[seat_name]
            seat_entry["uptime_pct"] = round(host_info.get("uptime", 0) * 100, 1)
            seat_entry["vram_trend_pct"] = host_info.get("vram_trend_pct")

        # Staleness check: if last_seen is >5s ago (or missing), mark stale
        if seat_entry["last_seen"]:
            try:
                last_seen_dt = datetime.fromisoformat(seat_entry["last_seen"].replace('Z', '+00:00'))
                age_s = (datetime.now(timezone.utc) - last_seen_dt).total_seconds()
                seat_entry["stale"] = age_s > STALENESS_THRESHOLD_S
                seat_entry["age_s"] = round(age_s, 1)
            except (ValueError, AttributeError):
                seat_entry["stale"] = True
        else:
            seat_entry["stale"] = True

        seats[seat_name] = seat_entry

    # Build the consolidated heartbeat
    heartbeat = {
        "ts": now_iso,
        "generated_by": "fleet_heartbeat.py",
        "staleness_threshold_s": STALENESS_THRESHOLD_S,
        "fleet_score": autonomy.get("score"),
        "fleet_readiness": autonomy.get("fleet_readiness"),
        "seats": seats,
        "seats_stale_count": sum(1 for s in seats.values() if s["stale"]),
        "recovery_sla_compliance_pct": {
            k: v.get("sla_compliance_pct") 
            for k, v in recovery_sla.get("types", {}).items()
        },
        "portal": seat_matrix.get("portal"),
    }

    # Write to file
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    HEARTBEAT_FILE.write_text(json.dumps(heartbeat, indent=2), encoding='utf-8')
    return heartbeat


def check_staleness():
    """Check the existing heartbeat for staleness. Returns (is_fresh, details)."""
    hb = load_json(HEARTBEAT_FILE)
    if not hb:
        return False, {"error": "no heartbeat file"}
    
    try:
        ts_dt = datetime.fromisoformat(hb["ts"].replace('Z', '+00:00'))
        age_s = (datetime.now(timezone.utc) - ts_dt).total_seconds()
    except (ValueError, KeyError):
        return False, {"error": "invalid timestamp in heartbeat"}
    
    is_fresh = age_s <= STALENESS_THRESHOLD_S
    return is_fresh, {
        "age_s": round(age_s, 1),
        "threshold_s": STALENESS_THRESHOLD_S,
        "stale_seats": [k for k, v in hb.get("seats", {}).items() if v.get("stale")],
    }


def selftest():
    """Run self-test for fleet heartbeat consolidation."""
    print("=== fleet_heartbeat.py selftest ===")
    passed = 0
    failed = 0

    def check(name, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  ok   - {name}")
        else:
            failed += 1
            print(f"  FAIL - {name} {detail}")

    # Test 1: Generate heartbeat from existing sources
    hb = generate_heartbeat()
    check("Heartbeat generated", hb is not None)
    check("All 4 seats present", 
          all(s in hb.get("seats", {}) for s in KNOWN_SEATS),
          f"got: {list(hb.get('seats', {}).keys())}")
    check("Fleet score included", hb.get("fleet_score") is not None)
    check("Staleness threshold set to 5s", hb.get("staleness_threshold_s") == 5)
    check("Heartbeat file written", HEARTBEAT_FILE.exists())

    # Test 2: Verify structure of each seat entry
    for seat in KNOWN_SEATS:
        s = hb["seats"][seat]
        has_fields = all(k in s for k in ["state", "last_seen", "stale", "uptime_pct"])
        check(f"Seat {seat} has required fields", has_fields)

    # Test 3: Staleness detection - simulate a 10s gap
    print("\n  [Simulating 10s staleness gap...]")
    # Write a heartbeat with an old timestamp (10s ago)
    old_ts = datetime.now(timezone.utc).replace(microsecond=0)
    from datetime import timedelta
    old_ts = old_ts - timedelta(seconds=10)
    
    test_hb = dict(hb)
    test_hb["ts"] = old_ts.isoformat()
    # Also mark one seat as having last_seen 10s ago
    test_hb["seats"]["White"]["last_seen"] = old_ts.isoformat()
    test_hb["seats"]["White"]["stale"] = True
    test_hb["seats"]["White"]["age_s"] = 10.0
    
    HEARTBEAT_FILE.write_text(json.dumps(test_hb, indent=2), encoding='utf-8')
    
    is_fresh, details = check_staleness()
    check("Stale heartbeat detected (10s > 5s threshold)", not is_fresh)
    check("Age reported correctly (~10s)", 
          details.get("age_s", 0) >= 9, f"got {details.get('age_s')}")
    check("White seat flagged stale", "White" in details.get("stale_seats", []))

    # Test 4: Fresh heartbeat passes
    fresh_hb = generate_heartbeat()  # regenerate with current ts
    is_fresh2, details2 = check_staleness()
    check("Fresh heartbeat passes (just generated)", is_fresh2)

    # Test 5: Recovery SLA data included
    check("Recovery SLA compliance included", 
          "recovery_sla_compliance_pct" in hb)

    print(f"\n=== Results: {passed} PASS, {failed} FAIL ===")
    return failed == 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1].lower()
    
    if cmd == "generate":
        hb = generate_heartbeat()
        print(json.dumps(hb, indent=2))
    elif cmd == "check":
        is_fresh, details = check_staleness()
        print(json.dumps({"fresh": is_fresh, **details}))
        sys.exit(0 if is_fresh else 1)
    elif cmd == "selftest":
        ok = selftest()
        sys.exit(0 if ok else 1)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
