#!/usr/bin/env python3
"""recovery_trend.py — Autonomous Recovery Time Trend Analysis.

Goal: #7 Autonomous Recovery Time Trend Analysis
From recovery/incident data, compute rolling 7-day mean + p95 for each incident type;
verify the trend is non-degrading (each window <= previous * 1.1); alert if any metric
degrades >10%.

Verified: current window computed for all tracked incident types; trend direction reported
per type; a synthetic degradation spike (>15%) injected into test data is correctly flagged.
"""
import json, re, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INCIDENTS_FILE = REPO_ROOT / "memory" / "ops" / "incidents.jsonl"
HEAL_LOG_FILE = REPO_ROOT / "memory" / "ops" / "portal-heal-log.jsonl"
GUARDIAN_LOG = REPO_ROOT / "memory" / "ops" / "guardian-log.jsonl"
RESULTS_FILE = REPO_ROOT / "memory" / "ops" / "recovery-trend-results.json"

ROLLING_WINDOW_DAYS = 7
DEGRADATION_THRESHOLD = 0.10  # 10%


def parse_ts(s):
    if not s:
        return None
    s = s.strip()
    for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f+00:00", "%Y-%m-%dT%H:%M:%S+00:00"]:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def load_incidents():
    """Load incidents with inferred recovery times."""
    if not INCIDENTS_FILE.exists():
        return []
    
    # Load all heal/recovery events to match against incidents
    recovery_times = []  # list of (ts, type) for health_check_ok / portal-start
    
    if HEAL_LOG_FILE.exists():
        for line in HEAL_LOG_FILE.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                ts = parse_ts(e.get("timestamp", ""))
                if ts and e.get("event") == "health_check_ok":
                    recovery_times.append((ts, "portal_heal"))
            except json.JSONDecodeError:
                continue
    
    if GUARDIAN_LOG.exists():
        for line in GUARDIAN_LOG.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                ts = parse_ts(e.get("t", ""))
                if ts and e.get("event") == "portal-start":
                    recovery_times.append((ts, "guardian_recovery"))
            except json.JSONDecodeError:
                continue
    
    recovery_times.sort(key=lambda x: x[0])
    
    incidents = []
    for line in INCIDENTS_FILE.read_text(encoding="utf-8").strip().split("\n"):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        ts = parse_ts(e.get("timestamp", ""))
        if not ts:
            continue
        
        inc_type = e.get("incident", {}).get("type", "unknown")
        
        # Find first recovery event after this incident
        recovery_ts = None
        for rt, _ in recovery_times:
            if rt > ts:
                recovery_ts = rt
                break
        
        if recovery_ts:
            recovery_s = (recovery_ts - ts).total_seconds()
        else:
            recovery_s = None  # No recovery observed
        
        incidents.append({
            "ts": ts,
            "type": inc_type,
            "recovery_s": recovery_s,
        })
    
    return incidents


def compute_trend(incidents):
    """Compute rolling window stats per incident type and check for degradation."""
    now = datetime.now(timezone.utc)
    results = {}
    
    types = set(i["type"] for i in incidents if i["recovery_s"] is not None)
    
    for itype in sorted(types):
        typed = [i for i in incidents if i["type"] == itype and i["recovery_s"] is not None]
        if not typed:
            continue
        
        # Current window (last 7 days)
        current = [i["recovery_s"] for i in typed 
                   if i["ts"] >= now - timedelta(days=ROLLING_WINDOW_DAYS)]
        
        # Previous window (7-14 days ago)
        previous = [i["recovery_s"] for i in typed 
                    if now - timedelta(days=ROLLING_WINDOW_DAYS * 2) <= i["ts"] < now - timedelta(days=ROLLING_WINDOW_DAYS)]
        
        entry = {"count": len(typed)}
        
        if current:
            entry["current_mean_s"] = round(mean(current), 1)
            sorted_c = sorted(current)
            p95_idx = int(0.95 * (len(sorted_c) - 1))
            entry["current_p95_s"] = round(sorted_c[p95_idx], 1)
        
        if previous:
            entry["previous_mean_s"] = round(mean(previous), 1)
            sorted_p = sorted(previous)
            p95_idx = int(0.95 * (len(sorted_p) - 1))
            entry["previous_p95_s"] = round(sorted_p[p95_idx], 1)
        
        # Check degradation
        if "current_mean_s" in entry and "previous_mean_s" in entry:
            prev_mean = entry["previous_mean_s"]
            curr_mean = entry["current_mean_s"]
            if prev_mean > 0:
                change = (curr_mean - prev_mean) / prev_mean
                entry["trend_change_pct"] = round(change * 100, 1)
                entry["degrading"] = change > DEGRADATION_THRESHOLD
                entry["alert"] = change > DEGRADATION_THRESHOLD
            else:
                entry["trend_change_pct"] = None
                entry["degrading"] = False
                entry["alert"] = False
        
        if "current_mean_s" not in entry:
            entry["note"] = "insufficient data in current window"
        
        results[itype] = entry
    
    return results


def self_test():
    """Self-test with synthetic data."""
    print("[SELF-TEST] recovery_trend.py")
    all_pass = True
    
    # T1: Synthetic stable trend (no degradation)
    now = datetime.now(timezone.utc)
    stable_incidents = []
    for i in range(4):  # Previous window
        stable_incidents.append({
            "ts": now - timedelta(days=10, hours=i),
            "type": "host_down",
            "recovery_s": 120.0 + i * 5,  # 120-135s
        })
    for i in range(4):  # Current window
        stable_incidents.append({
            "ts": now - timedelta(days=3, hours=i),
            "type": "host_down",
            "recovery_s": 125.0 + i * 3,  # 125-134s (similar)
        })
    result = compute_trend(stable_incidents)
    ok = not result["host_down"].get("degrading", False)
    print(f"  {'PASS' if ok else 'FAIL'} T1_stable_no_degradation: degrading={result['host_down'].get('degrading')}")
    all_pass = all_pass and ok
    
    # T2: Synthetic degradation spike (>15%)
    degraded_incidents = []
    for i in range(4):  # Previous window: fast recovery
        degraded_incidents.append({
            "ts": now - timedelta(days=10, hours=i),
            "type": "host_down",
            "recovery_s": 60.0,  # 60s
        })
    for i in range(4):  # Current window: much slower
        degraded_incidents.append({
            "ts": now - timedelta(days=3, hours=i),
            "type": "host_down",
            "recovery_s": 100.0,  # 100s (67% increase)
        })
    result = compute_trend(degraded_incidents)
    ok = result["host_down"].get("degrading", False) and result["host_down"].get("alert", False)
    print(f"  {'PASS' if ok else 'FAIL'} T2_degradation_flagged: change={result['host_down'].get('trend_change_pct')}%, alert={result['host_down'].get('alert')}")
    all_pass = all_pass and ok
    
    # T3: Multiple incident types tracked independently
    multi_incidents = []
    for i in range(3):
        multi_incidents.append({"ts": now - timedelta(days=10, hours=i), "type": "host_down", "recovery_s": 90.0})
        multi_incidents.append({"ts": now - timedelta(days=10, hours=i+1), "type": "portal_down", "recovery_s": 30.0})
    for i in range(3):
        multi_incidents.append({"ts": now - timedelta(days=3, hours=i), "type": "host_down", "recovery_s": 95.0})
        multi_incidents.append({"ts": now - timedelta(days=3, hours=i+1), "type": "portal_down", "recovery_s": 200.0})  # degraded!
    result = compute_trend(multi_incidents)
    ok = (not result["host_down"].get("degrading", False)) and result["portal_down"].get("degrading", False)
    print(f"  {'PASS' if ok else 'FAIL'} T3_multi_type_independent: host_down={result['host_down'].get('degrading')}, portal_down={result['portal_down'].get('degrading')}")
    all_pass = all_pass and ok
    
    # T4: No data in current window (graceful)
    sparse_incidents = [
        {"ts": now - timedelta(days=20), "type": "rare_event", "recovery_s": 50.0},
    ]
    result = compute_trend(sparse_incidents)
    ok = "current_mean_s" not in result.get("rare_event", {}) or "note" in result.get("rare_event", {})
    print(f"  {'PASS' if ok else 'FAIL'} T4_sparse_graceful: keys={list(result.get('rare_event', {}).keys())}")
    all_pass = all_pass and ok
    
    # T5: P95 computation correct
    p95_incidents = []
    for i in range(20):  # 20 values in current window
        p95_incidents.append({"ts": now - timedelta(days=1, hours=i), "type": "test", "recovery_s": float(i + 1)})
    result = compute_trend(p95_incidents)
    # P95 of [1..20] should be ~19
    ok = result["test"].get("current_p95_s") is not None and 18 <= result["test"]["current_p95_s"] <= 20
    print(f"  {'PASS' if ok else 'FAIL'} T5_p95_correct: p95={result['test'].get('current_p95_s')} (expected ~19)")
    all_pass = all_pass and ok
    
    # T6: Zero previous window (can't compute trend, no crash)
    only_current = [
        {"ts": now - timedelta(days=2), "type": "new_type", "recovery_s": 80.0},
    ]
    result = compute_trend(only_current)
    ok = "trend_change_pct" not in result.get("new_type", {}) or result["new_type"].get("trend_change_pct") is None
    print(f"  {'PASS' if ok else 'FAIL'} T6_no_previous_window: trend={result['new_type'].get('trend_change_pct')}")
    all_pass = all_pass and ok
    
    passed = sum(1 for _ in [1])  # count via all_pass
    print(f"[SELF-TEST] {'ALL PASS' if all_pass else 'FAILURES'} (6 tests)")
    return all_pass


def main():
    if "--self-test" in sys.argv:
        ok = self_test()
        sys.exit(0 if ok else 1)
    
    print(f"[recovery_trend] Rolling {ROLLING_WINDOW_DAYS}-day window analysis")
    incidents = load_incidents()
    with_recovery = [i for i in incidents if i["recovery_s"] is not None]
    print(f"  Total incidents: {len(incidents)}, with recovery: {len(with_recovery)}")
    
    results = compute_trend(incidents)
    alerts = []
    
    for itype, stats in sorted(results.items()):
        print(f"  Type '{itype}': count={stats['count']}", end="")
        if "current_mean_s" in stats:
            print(f", current_mean={stats['current_mean_s']}s, p95={stats.get('current_p95_s','?')}s", end="")
        if "trend_change_pct" in stats and stats["trend_change_pct"] is not None:
            print(f", trend={stats['trend_change_pct']:+.1f}%", end="")
            if stats.get("alert"):
                print(" ** DEGRADING **", end="")
                alerts.append(itype)
        if "note" in stats:
            print(f" ({stats['note']})", end="")
        print()
    
    all_pass = len(alerts) == 0
    print(f"  RESULT: {'PASS' if all_pass else 'FAIL'} (alerts: {alerts})")
    
    # Save results
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    out = {"ts": datetime.now(timezone.utc).isoformat(), "incidents_total": len(incidents),
           "with_recovery": len(with_recovery), "results": results, "alerts": alerts}
    RESULTS_FILE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
