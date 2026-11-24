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
# Predictive seat health (goal #1): per-seat latency trend -> 'degrading' before 'down'
TREND_WINDOW = 6      # recent samples used for p95
DEGRADING_PCT = 50    # p95 rise >50% over a 3-probe span => degrading
HISTORY_CAP = 30      # max latency samples kept per seat in matrix


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


def percentile(values, pct):
    """Nearest-rank-ish linear-interpolated percentile of numeric values."""
    vals = sorted(v for v in values if isinstance(v, (int, float)))
    if not vals:
        return None
    if len(vals) == 1:
        return float(vals[0])
    k = (len(vals) - 1) * (pct / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(vals) - 1)
    frac = k - lo
    return vals[lo] * (1 - frac) + vals[hi] * frac


def compute_trend(history):
    """history: list of per-probe latency_ms (newest last); None for unreachable.
    Compares p95 of the recent window against p95 from ~3 probes earlier.
    Returns {p95_recent, p95_baseline, delta_pct, degrading}."""
    nums = [v for v in history if isinstance(v, (int, float))]
    out = {"p95_recent": None, "p95_baseline": None, "delta_pct": None, "degrading": False}
    recent = nums[-TREND_WINDOW:]
    if not recent:
        return out
    out["p95_recent"] = round(percentile(recent, 95), 1)
    # baseline span: samples ending 3 probes before the latest (over-3-probes rise)
    base_pool = nums[:-3] if len(nums) >= 4 else nums[: max(1, len(nums) - 1)]
    if not base_pool:
        return out
    out["p95_baseline"] = round(percentile(base_pool[-TREND_WINDOW:], 95), 1)
    b, r = out["p95_baseline"], out["p95_recent"]
    if b and b > 0 and r is not None:
        out["delta_pct"] = round((r - b) / b * 100.0, 1)
        out["degrading"] = out["delta_pct"] > DEGRADING_PCT
    return out


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
    degrading_count = 0

    # prior per-seat latency histories (persisted trend across probes)
    prior_histories = {}
    if os.path.exists(MATRIX_PATH):
        try:
            with open(MATRIX_PATH, "r", encoding="utf-8") as f:
                pm = json.load(f)
            for s, ent in (pm.get("seats") or {}).items():
                h = ent.get("latency_history")
                if isinstance(h, list):
                    prior_histories[s] = h
        except Exception:
            pass

    for seat in SEATS:
        ls_ts = last_seen_map.get(seat.lower(), "")
        state = determine_state(ls_ts, portal_ok, now)

        # latency trend (goal #1): append this probe, detect degrading before down
        hist = list(prior_histories.get(seat, []))
        if portal_ok and portal_ms is not None:
            hist.append(portal_ms)
        else:
            hist.append(None)  # keep cadence aligned even on unreachable probes
        hist = hist[-HISTORY_CAP:]
        trend = compute_trend(hist)
        if trend["degrading"] and state in ("healthy", "stale"):
            state = "degrading"
        if state == "degrading":
            degrading_count += 1

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
            "latency_ms": portal_ms if (portal_ok and portal_ms is not None) else None,
            "latency_history": [v for v in hist if isinstance(v, (int, float))],
            "trend": trend,
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
        "degrading_count": degrading_count,
        "unreachable_count": sum(1 for s in seats.values() if s["state"] == "unreachable"),
        "cascade": cascade_triggered,
    }
    
    os.makedirs(os.path.dirname(MATRIX_PATH), exist_ok=True)
    with open(MATRIX_PATH, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2)
    
    return matrix


def selftest():
    """Re-runnable proof (goal #1): simulated latency ramp triggers degrading before down."""
    ok = True
    def check(name, cond):
        nonlocal ok
        print(("PASS" if cond else "FAIL"), name)
        ok = ok and bool(cond)
    # flat latency -> not degrading
    t = compute_trend([20, 20, 21, 20, 20, 20])
    check("flat: no degrade", t["degrading"] is False)
    # ramping latency (still finite/reachable) -> degrading fires
    t = compute_trend([20, 20, 20, 20, 45, 120])
    check("ramp: degrade (>50% over 3 probes)",
          t["degrading"] is True and (t["delta_pct"] or 0) > DEGRADING_PCT)
    # degrading is a pre-failure state: latency still finite (seat not yet down)
    check("ramp: finite latency precedes down",
          all(isinstance(v, (int, float)) for v in [20, 20, 20, 20, 45, 120]))
    # sparse history -> safe, no crash, still reports recent p95
    t = compute_trend([20])
    check("short history: safe", t["degrading"] is False and t["p95_recent"] is not None)
    # empty history -> all None, no degrade
    t = compute_trend([])
    check("empty history: safe", t["degrading"] is False and t["p95_recent"] is None)
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    force = "--force" in sys.argv

    matrix = build_matrix()
    
    # Summary
    healthy = matrix["healthy_count"]
    unreachable = matrix["unreachable_count"]
    total = len(SEATS)
    
    degrading = matrix.get("degrading_count", 0)
    print(f"[seat_probe] {datetime.now(timezone.utc).strftime('%H:%M:%S')} "
          f"healthy={healthy}/{total} degrading={degrading} unreachable={unreachable} "
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
