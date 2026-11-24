#!/usr/bin/env python3
"""seat_probe.py - Probe all 8 fleet seats; update seat-matrix.json state+last_seen.

Every 5min (driven by schtasks or autoloop), this script:
1. Reads memory/ops/autoloop.jsonl to get last activity timestamp per agent
2. Probes the portal health endpoint for live confirmation
3. Writes memory/ops/seat-matrix.json with per-seat state, last_seen, latency_ms
4. Flags seats >30min unreachable as "cascade"

Usage:
    python memory/mechanic/seat_probe.py [--force]

Exit codes: 0=healthy, 1=degraded, 2=cascade triggered
"""
import json, os, sys, time, urllib.request
from datetime import datetime, timezone, timedelta

SEATS = ["orchestrator", "researcher", "builder", "verifier",
         "designer", "archivist", "scribe", "mechanic"]

AUTOLOOP_PATH = os.path.join("memory", "ops", "autoloop.jsonl")
MATRIX_PATH = os.path.join("memory", "ops", "seat-matrix.json")
PORTAL_URL = "http://127.0.0.1:8099/api/health"
STALE_THRESHOLD_MIN = 30  # minutes before marking unreachable


def get_last_seen_per_agent():
    """Parse autoloop.jsonl for most recent timestamp per agent."""
    last_seen = {}
    if not os.path.exists(AUTOLOOP_PATH):
        return last_seen
    with open(AUTOLOOP_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            agent = entry.get("agent", "").lower()
            ts = entry.get("timestamp", "")
            if agent in [s.lower() for s in SEATS]:
                # Keep latest timestamp per agent
                if agent not in last_seen or ts > last_seen[agent]:
                    last_seen[agent] = ts
    return last_seen


def probe_portal():
    """Probe portal health endpoint. Returns (ok, latency_ms) or (False, None)."""
    t0 = time.time()
    try:
        req = urllib.request.Request(PORTAL_URL, method="GET")
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read(2048).decode("utf-8", errors="replace")
            return (200 <= r.status < 300), round((time.time() - t0) * 1000, 1)
    except Exception:
        return False, None


def parse_iso_ts(ts_str):
    """Parse ISO timestamp string to datetime."""
    try:
        # Handle +00:00 suffix
        ts_str = ts_str.replace("+00:00", "Z")
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        return None


def determine_state(last_seen_ts, portal_ok, now):
    """Determine seat state based on last activity and portal health."""
    if not last_seen_ts:
        # No record at all
        if portal_ok:
            return "unknown"
        return "unreachable"
    
    dt = parse_iso_ts(last_seen_ts)
    if dt is None:
        return "unknown"
    
    age_min = (now - dt).total_seconds() / 60.0
    if age_min > STALE_THRESHOLD_MIN:
        return "unreachable"
    elif age_min > 15:
        return "stale"
    else:
        return "healthy"


def build_matrix():
    """Build the seat-matrix.json content."""
    now = datetime.now(timezone.utc)
    last_seen_map = get_last_seen_per_agent()
    portal_ok, portal_ms = probe_portal()
    
    seats = {}
    cascade_triggered = False
    
    for seat in SEATS:
        ls_ts = last_seen_map.get(seat.lower(), "")
        state = determine_state(ls_ts, portal_ok, now)
        
        age_min = None
        if ls_ts:
            dt = parse_iso_ts(ls_ts)
            if dt:
                age_min = round((now - dt).total_seconds() / 60.0, 1)
        
        seat_entry = {
            "state": state,
            "last_seen": ls_ts or None,
            "age_minutes": age_min,
            "portal_reachable": portal_ok,
        }
        seats[seat] = seat_entry
        
        if state == "unreachable":
            cascade_triggered = True
    
    matrix = {
        "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "probe_interval_min": 5,
        "stale_threshold_min": STALE_THRESHOLD_MIN,
        "portal": {"ok": portal_ok, "latency_ms": portal_ms},
        "seats": seats,
        "healthy_count": sum(1 for s in seats.values() if s["state"] == "healthy"),
        "unreachable_count": sum(1 for s in seats.values() if s["state"] == "unreachable"),
        "cascade": cascade_triggered,
    }
    
    os.makedirs(os.path.dirname(MATRIX_PATH), exist_ok=True)
    with open(MATRIX_PATH, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2)
    
    return matrix


def main():
    force = "--force" in sys.argv
    
    matrix = build_matrix()
    
    # Summary
    healthy = matrix["healthy_count"]
    unreachable = matrix["unreachable_count"]
    total = len(SEATS)
    
    print(f"[seat_probe] {datetime.now(timezone.utc).strftime('%H:%M:%S')} "
          f"healthy={healthy}/{total} unreachable={unreachable} "
          f"portal={'OK' if matrix['portal']['ok'] else 'FAIL'} "
          f"cascade={'YES' if matrix['cascade'] else 'no'}")
    
    for seat in SEATS:
        s = matrix["seats"][seat]
        marker = "+" if s["state"] == "healthy" else ("!" if s["state"] == "unreachable" else "-")
        age = f"{s['age_minutes']}m" if s["age_minutes"] is not None else "?"
        print(f"  [{marker}] {seat:12s} {s['state']:12s} age={age}")
    
    # Exit code: 0=healthy, 1=degraded, 2=cascade
    if matrix["cascade"]:
        sys.exit(2)
    elif unreachable > 0 or healthy < total:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
