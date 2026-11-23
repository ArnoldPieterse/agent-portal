#!/usr/bin/env python3
"""Alert Correlation Engine - Builder cycle-14 goal #3.

Groups individual alerts into correlated incidents based on:
  - Temporal proximity (alerts within CORRELATION_WINDOW_S of each other)
  - Shared scope (same host or same agent)
  - Type affinity (related alert types cluster together)

Input: memory/ops/alerts.jsonl (one alert per line)
Output: memory/builder/incidents.jsonl (grouped incidents with severity + summary)

Selftest verifies:
  AC1: 3 alerts on same host within 60s -> 1 incident
  AC2: 2 alerts on different hosts >5min apart -> 2 separate incidents
  AC3: Mixed batch produces correct grouping count
  AC4: Incident severity = max of member severities
  AC5: Output is valid JSONL with required fields
"""
import json, sys, os, datetime
from collections import defaultdict

ALERTS_FILE = "memory/ops/alerts.jsonl"
OUTPUT_FILE = "memory/builder/incidents.jsonl"
CORRELATION_WINDOW_S = 300  # 5 minutes


def parse_ts(val):
    """Parse timestamp to epoch seconds; returns None on failure."""
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            return val
        s = str(val)
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.datetime.strptime(s, fmt)
                return dt.timestamp()
            except ValueError:
                continue
        return None
    except Exception:
        return None


def load_alerts(path=ALERTS_FILE):
    if not os.path.exists(path):
        return []
    alerts = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    a = json.loads(line)
                    a["_ts"] = parse_ts(a.get("ts") or a.get("timestamp"))
                    alerts.append(a)
                except json.JSONDecodeError:
                    pass
    return [a for a in alerts if a.get("_ts") is not None]


def correlate(alerts):
    """Group alerts into incidents using greedy temporal+scope clustering."""
    if not alerts:
        return []
    # Sort by time
    alerts = sorted(alerts, key=lambda a: a["_ts"])
    used = [False] * len(alerts)
    incidents = []

    for i in range(len(alerts)):
        if used[i]:
            continue
        seed = alerts[i]
        group = [seed]
        used[i] = True
        scope_keys = _scope_keys(seed)

        for j in range(i + 1, len(alerts)):
            if used[j]:
                continue
            candidate = alerts[j]
            # Temporal check: within window of seed
            if (candidate["_ts"] - seed["_ts"]) > CORRELATION_WINDOW_S:
                break
            # Scope check: shares at least one scope key with the group
            cand_keys = _scope_keys(candidate)
            if scope_keys & cand_keys:
                group.append(candidate)
                used[j] = True
                scope_keys |= cand_keys  # expand scope as group grows

        incidents.append(_make_incident(group))

    return incidents


def _scope_keys(alert):
    """Extract scope identifiers for correlation."""
    keys = set()
    host = alert.get("host") or alert.get("source_host")
    agent = alert.get("agent") or alert.get("source_agent")
    if host:
        keys.add(f"host:{host}")
    if agent:
        keys.add(f"agent:{agent}")
    # Fallback: use 'type' prefix as weak scope
    atype = alert.get("type", "")
    if atype:
        keys.add(f"type_prefix:{atype.split('_')[0]}")
    return keys


def _make_incident(group):
    """Build incident record from a group of correlated alerts."""
    severities = [a.get("severity", "info") for a in group]
    sev_order = {"critical": 4, "error": 3, "warning": 2, "info": 1}
    max_sev = max(severities, key=lambda s: sev_order.get(s, 0))

    types = list({a.get("type", "unknown") for a in group})
    hosts = list({a.get("host", "") for a in group if a.get("host")})
    agents = list({a.get("agent", "") for a in group if a.get("agent")})

    ts_list = [a["_ts"] for a in group]
    duration_s = max(ts_list) - min(ts_list) if len(ts_list) > 1 else 0

    return {
        "incident_id": f"inc-{min(a['_ts'] for a in group):.0f}-{len(group)}",
        "severity": max_sev,
        "alert_count": len(group),
        "types": sorted(types),
        "hosts": sorted(set(h for h in hosts if h)),
        "agents": sorted(set(a for a in agents if a)),
        "first_ts": min(ts_list),
        "last_ts": max(ts_list),
        "duration_s": round(duration_s, 1),
        "summary": f"{len(group)} alert(s) [{max_sev}] on {', '.join(hosts or agents) or 'unknown'}",
    }


def emit(incidents, path=OUTPUT_FILE):
    with open(path, "w", encoding="utf-8") as fh:
        for inc in incidents:
            fh.write(json.dumps(inc, ensure_ascii=False) + "\n")
    return path


def selftest():
    print("=" * 60)
    print("alert_correlator.py - SELFTEST")
    print("=" * 60)
    passed = 0
    base_ts = datetime.datetime(2026, 11, 23, 12, 0, 0).timestamp()

    # AC1: 3 alerts same host within 60s -> 1 incident
    alerts1 = [
        {"ts": base_ts, "host": "white", "type": "vram_high", "severity": "warning"},
        {"ts": base_ts + 20, "host": "white", "type": "cpu_high", "severity": "error"},
        {"ts": base_ts + 40, "host": "white", "type": "temp_high", "severity": "warning"},
    ]
    for a in alerts1:
        a["_ts"] = parse_ts(a["ts"]) if isinstance(a["ts"], str) else a["ts"]
    incs = correlate(alerts1)
    ac1 = len(incs) == 1 and incs[0]["alert_count"] == 3
    print(f"AC1: 3 same-host alerts -> 1 incident (got {len(incs)}) -> {'PASS' if ac1 else 'FAIL'}")
    passed += ac1

    # AC2: 2 alerts different hosts >5min apart -> 2 incidents
    alerts2 = [
        {"ts": base_ts, "host": "white", "type": "vram_high", "severity": "warning"},
        {"ts": base_ts + 600, "host": "black", "type": "oom", "severity": "critical"},
    ]
    for a in alerts2:
        a["_ts"] = parse_ts(a["ts"]) if isinstance(a["ts"], str) else a["ts"]
    incs = correlate(alerts2)
    ac2 = len(incs) == 2
    print(f"AC2: 2 different-host far-apart -> 2 incidents (got {len(incs)}) -> {'PASS' if ac2 else 'FAIL'}")
    passed += ac2

    # AC3: Mixed batch - 4 alerts, 2 clusters expected
    alerts3 = [
        {"ts": base_ts, "host": "white", "type": "vram_high", "severity": "warning"},
        {"ts": base_ts + 30, "host": "white", "type": "cpu_high", "severity": "error"},
        {"ts": base_ts + 400, "host": "black", "type": "oom", "severity": "critical"},
        {"ts": base_ts + 420, "host": "black", "type": "vram_high", "severity": "warning"},
    ]
    for a in alerts3:
        a["_ts"] = parse_ts(a["ts"]) if isinstance(a["ts"], str) else a["ts"]
    incs = correlate(alerts3)
    ac3 = len(incs) == 2 and {i["alert_count"] for i in incs} == {2, 2}
    print(f"AC3: mixed batch -> 2 incidents of 2 (got {[i['alert_count'] for i in incs]}) -> {'PASS' if ac3 else 'FAIL'}")
    passed += ac3

    # AC4: Severity = max of members
    alerts4 = [
        {"ts": base_ts, "host": "white", "type": "a", "severity": "info"},
        {"ts": base_ts + 10, "host": "white", "type": "b", "severity": "critical"},
    ]
    for a in alerts4:
        a["_ts"] = parse_ts(a["ts"]) if isinstance(a["ts"], str) else a["ts"]
    incs = correlate(alerts4)
    ac4 = len(incs) == 1 and incs[0]["severity"] == "critical"
    print(f"AC4: severity=max (got {incs[0]['severity'] if incs else 'N/A'}) -> {'PASS' if ac4 else 'FAIL'}")
    passed += ac4

    # AC5: Output valid JSONL with required fields
    emit(incs)
    with open(OUTPUT_FILE, encoding="utf-8") as fh:
        lines = [l.strip() for l in fh if l.strip()]
    all_valid = True
    required = {"incident_id", "severity", "alert_count", "types", "first_ts"}
    for line in lines:
        obj = json.loads(line)
        if not required.issubset(obj.keys()):
            all_valid = False
            break
    ac5 = all_valid and len(lines) >= 1
    print(f"AC5: output valid JSONL with required fields -> {'PASS' if ac5 else 'FAIL'}")
    passed += ac5

    print(f"\nRESULT: {passed}/5 ACs PASSED")
    return 0 if passed == 5 else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    alerts = load_alerts()
    if not alerts:
        print(f"No alerts found at {ALERTS_FILE}")
        # Try decision log as fallback source
        dl_path = "memory/ops/decision-log.jsonl"
        if os.path.exists(dl_path):
            with open(dl_path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                        t = e.get("type", "")
                        if any(k in t.lower() for k in ("alert", "fail", "error", "oom")):
                            e["_ts"] = parse_ts(e.get("ts") or e.get("timestamp"))
                            alerts.append(e)
                    except json.JSONDecodeError:
                        pass
    if not alerts:
        print("No correlatable alerts found. Nothing to do.")
        return 0
    incidents = correlate(alerts)
    emit(incidents)
    print(f"Correlated {len(alerts)} alerts -> {len(incidents)} incidents")
    for inc in incidents:
        print(f"  [{inc['severity']}] {inc['summary']} ({inc['duration_s']}s)")
    print(f"Output: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
