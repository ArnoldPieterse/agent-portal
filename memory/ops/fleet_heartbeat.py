#!/usr/bin/env python3
"""fleet_heartbeat.py - Generate unified fleet heartbeat from 3 source files.

Merges: seat-matrix.json + autonomy-score.json + recovery-sla-summary.json
Output: memory/ops/fleet-heartbeat.json (<2KB, all 4 seats + composite score)

Run every probe cycle (5 min) via schtask or inline from other scripts.
"""
import json, datetime, os
from pathlib import Path

OUT = Path("memory/ops/fleet-heartbeat.json")
SOURCES = {
    "seat_matrix": Path("memory/ops/seat-matrix.json"),
    "autonomy_score": Path("memory/ops/autonomy-score.json"),
    "recovery_sla": Path("memory/ops/recovery-sla-summary.json"),
}

STALE_THRESHOLD_S = 5 * 60  # 5 min probe interval


def load_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def compute_age_s(ts_str):
    """Compute age in seconds from an ISO timestamp string."""
    if not ts_str:
        return None
    try:
        dt = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        return (now - dt).total_seconds()
    except Exception:
        return None


# Agent-to-host mapping (derived from placement-architecture + fleet_reload.py)
AGENT_TO_HOST = {
    "orchestrator": "white", "researcher": "white", "mechanic": "red",
    "builder": "pale", "verifier": "black", "designer": "black",
    "scribe": "white", "archivist": "red", "pixel": "pale", "forge": "black",
}


def build_heartbeat():
    sm = load_json(SOURCES["seat_matrix"])
    as_ = load_json(SOURCES["autonomy_score"])
    sla = load_json(SOURCES["recovery_sla"])
    
    # Build per-HOST state by aggregating agent states on that host
    hosts = {"White": {}, "Red": {}, "Pale": {}, "Black": {}}
    matrix_seats = sm.get("seats", {})
    
    for agent_name, info in matrix_seats.items():
        host_key = AGENT_TO_HOST.get(agent_name, "white")  # default to white
        host_display = host_key.capitalize()
        last_seen = info.get("last_seen")
        age_s = compute_age_s(last_seen) if last_seen else None
        stale = (age_s is not None and age_s > STALE_THRESHOLD_S * 60) or \
                info.get("state") == "unreachable"
        state = info.get("state", "unknown")
        latency = info.get("latency_ms")
        
        h = hosts[host_display]
        # Track worst state per host
        if state == "healthy":
            h["has_healthy"] = True
        if state == "unreachable":
            h["has_unreachable"] = True
        # Use most recent last_seen
        if "last_seen" not in h or (last_seen and last_seen > h.get("last_seen", "")):
            h["last_seen"] = last_seen
            h["age_s"] = round(age_s, 1) if age_s else None
        # Use best latency
        if latency is not None:
            h["latency_ms"] = min(h.get("latency_ms", float('inf')), latency)
    
    # Finalize host entries
    seats = {}
    for name, h in hosts.items():
        has_h = h.get("has_healthy", False)
        has_u = h.get("has_unreachable", False)
        state = "healthy" if has_h and not has_u else ("degrading" if has_h else "unreachable")
        last_seen = h.get("last_seen")
        age_s = h.get("age_s")
        stale = (age_s is not None and age_s > STALE_THRESHOLD_S * 60) or state == "unreachable"
        seats[name] = {
            "state": state,
            "last_seen": last_seen,
            "latency_ms": h.get("latency_ms"),
            "uptime_pct": 100.0 if state == "healthy" else (50.0 if state == "degrading" else 0.0),
            "vram_trend_pct": 0.0,
            "stale": stale,
            "last_cycle_ts": None,
            "age_s": age_s,
        }
    
    # Composite score from autonomy-score.json
    fleet_score = as_.get("score", as_.get("fleet_score", 0.0))
    fleet_readiness = as_.get("readiness_pct", as_.get("fleet_readiness", 0.0))
    
    # Recovery SLA compliance
    sla_types = sla.get("types", {})
    recovery_compliance = {}
    for tname in ["cascade", "oom", "single_seat"]:
        if tname in sla_types:
            recovery_compliance[tname] = sla_types[tname].get("sla_compliance_pct", 0.0)
    
    # Portal status
    portal_ok = sm.get("portal", {}).get("ok", False)
    portal_latency = sm.get("portal", {}).get("latency_ms")
    
    heartbeat = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "generated_by": "fleet_heartbeat.py",
        "staleness_threshold_s": STALE_THRESHOLD_S,
        "fleet_score": fleet_score,
        "fleet_readiness": fleet_readiness,
        "seats": seats,
        "seats_stale_count": sum(1 for s in seats.values() if s["stale"]),
        "recovery_sla_compliance_pct": recovery_compliance,
        "portal": {"ok": portal_ok, "latency_ms": portal_latency},
    }
    
    # Write output
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(heartbeat, indent=2), encoding="utf-8")
    size = OUT.stat().st_size
    print(f"fleet-heartbeat.json written ({size}B, {'OK' if size < 2048 else 'OVER 2KB'})")
    return heartbeat


if __name__ == "__main__":
    build_heartbeat()