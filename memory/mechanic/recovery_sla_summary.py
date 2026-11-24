"""Recovery SLA Summary Data generator.

Reads memory/ops/recovery-times.jsonl and produces structured JSON:
  per-type mean, p95, trend, SLA compliance pct.
Output: memory/ops/recovery-sla-summary.json

SLA targets (from Verifier goal #5):
  single_seat: detection <5min, recovery <30min
  cascade:     detection <10min, recovery <120min
  oom:         detection <5min, recovery <60min

Usage:
  python memory/mechanic/recovery_sla_summary.py          # live (reads jsonl)
  python memory/mechanic/recovery_sla_summary.py --selftest  # simulated data
"""
import json, pathlib, statistics, datetime, sys, os

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
INPUT = BASE / "memory" / "ops" / "recovery-times.jsonl"
OUTPUT = BASE / "memory" / "ops" / "recovery-sla-summary.json"

SLA_TARGETS = {
    "single_seat": {"detection_min": 5, "recovery_min": 30},
    "cascade":     {"detection_min": 10, "recovery_min": 120},
    "oom":         {"detection_min": 5, "recovery_min": 60},
}

def percentile(values, p):
    """Compute p-th percentile (0-100) of a list."""
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (k - f) * (s[c] - s[f])

def compute_summary(records):
    """Compute per-type summary from list of incident dicts."""
    by_type = {}
    for r in records:
        t = r.get("type", "unknown")
        by_type.setdefault(t, []).append(r)

    summary = {"generated": datetime.datetime.now().isoformat(), "types": {}}

    for t, recs in sorted(by_type.items()):
        detections = [r["detection_min"] for r in recs if "detection_min" in r]
        recoveries = [r["recovery_min"] for r in recs if "recovery_min" in r]

        sla = SLA_TARGETS.get(t, {"detection_min": 5, "recovery_min": 30})
        det_ok = sum(1 for d in detections if d <= sla["detection_min"])
        rec_ok = sum(1 for r in recoveries if r <= sla["recovery_min"])

        # Trend: compare first half vs second half of recovery times
        trend = "stable"
        if len(recoveries) >= 4:
            mid = len(recoveries) // 2
            first_half = statistics.mean(recoveries[:mid])
            second_half = statistics.mean(recoveries[mid:])
            if second_half > first_half * 1.2:
                trend = "worsening"
            elif second_half < first_half * 0.8:
                trend = "improving"

        summary["types"][t] = {
            "count": len(recs),
            "detection_mean_min": round(statistics.mean(detections), 2) if detections else None,
            "detection_p95_min": round(percentile(detections, 95), 2) if detections else None,
            "recovery_mean_min": round(statistics.mean(recoveries), 2) if recoveries else None,
            "recovery_p95_min": round(percentile(recoveries, 95), 2) if recoveries else None,
            "trend": trend,
            "sla_target_detection_min": sla["detection_min"],
            "sla_target_recovery_min": sla["recovery_min"],
            "sla_compliance_pct": round(100.0 * (det_ok + rec_ok) / (len(detections) + len(recoveries)), 1) if (detections or recoveries) else None,
        }

    summary["total_incidents"] = len(records)
    return summary

def selftest():
    """Verify with simulated data: 3 incident types, compliance matches raw."""
    # Simulate 12 incidents across 3 types
    sim_records = [
        # single_seat: 4 incidents (3 within SLA, 1 over on recovery)
        {"type": "single_seat", "detection_min": 2.0, "recovery_min": 15.0, "ts": "2026-11-20T10:00:00"},
        {"type": "single_seat", "detection_min": 3.0, "recovery_min": 25.0, "ts": "2026-11-21T11:00:00"},
        {"type": "single_seat", "detection_min": 4.0, "recovery_min": 28.0, "ts": "2026-11-22T12:00:00"},
        {"type": "single_seat", "detection_min": 3.5, "recovery_min": 45.0, "ts": "2026-11-23T13:00:00"},
        # cascade: 4 incidents (3 within SLA, 1 over on recovery)
        {"type": "cascade", "detection_min": 8.0, "recovery_min": 90.0, "ts": "2026-11-20T14:00:00"},
        {"type": "cascade", "detection_min": 9.0, "recovery_min": 100.0, "ts": "2026-11-21T15:00:00"},
        {"type": "cascade", "detection_min": 7.0, "recovery_min": 110.0, "ts": "2026-11-22T16:00:00"},
        {"type": "cascade", "detection_min": 6.0, "recovery_min": 150.0, "ts": "2026-11-23T17:00:00"},
        # oom: 4 incidents (all within SLA)
        {"type": "oom", "detection_min": 3.0, "recovery_min": 30.0, "ts": "2026-11-20T09:00:00"},
        {"type": "oom", "detection_min": 4.0, "recovery_min": 45.0, "ts": "2026-11-21T10:00:00"},
        {"type": "oom", "detection_min": 2.5, "recovery_min": 50.0, "ts": "2026-11-22T11:00:00"},
        {"type": "oom", "detection_min": 3.5, "recovery_min": 40.0, "ts": "2026-11-23T12:00:00"},
    ]

    result = compute_summary(sim_records)
    errors = []

    # Check 1: all 3 types present
    expected_types = {"single_seat", "cascade", "oom"}
    if set(result["types"].keys()) != expected_types:
        errors.append(f"Types mismatch: got {set(result['types'].keys())}")

    # Check 2: compliance matches raw data (manual calc)
    # single_seat: det all ok (4/4), rec 3/4 -> 7/8 = 87.5%
    ss = result["types"]["single_seat"]
    if ss["sla_compliance_pct"] != 87.5:
        errors.append(f"single_seat compliance: expected 87.5, got {ss['sla_compliance_pct']}")

    # cascade: det all ok (4/4), rec 3/4 -> 7/8 = 87.5%
    cs = result["types"]["cascade"]
    if cs["sla_compliance_pct"] != 87.5:
        errors.append(f"cascade compliance: expected 87.5, got {cs['sla_compliance_pct']}")

    # oom: det all ok (4/4), rec all ok (4/4) -> 8/8 = 100%
    om = result["types"]["oom"]
    if om["sla_compliance_pct"] != 100.0:
        errors.append(f"oom compliance: expected 100.0, got {om['sla_compliance_pct']}")

    # Check 3: counts correct
    for t in expected_types:
        if result["types"][t]["count"] != 4:
            errors.append(f"{t} count: expected 4, got {result['types'][t]['count']}")

    # Check 4: trend detection - single_seat has worsening (15,25,28,45 -> second half higher)
    if ss["trend"] != "worsening":
        errors.append(f"single_seat trend: expected worsening, got {ss['trend']}")

    # Check 5: p95 values sane
    if ss["recovery_p95_min"] is None or ss["recovery_p95_min"] < 28:
        errors.append(f"single_seat recovery_p95 too low: {ss['recovery_p95_min']}")

    # Check 6: total count
    if result["total_incidents"] != 12:
        errors.append(f"total: expected 12, got {result['total_incidents']}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return False
    else:
        print("PASS: all 6 selftest checks OK")
        print(f"  types: {list(result['types'].keys())}")
        print(f"  compliance: ss={ss['sla_compliance_pct']}% cs={cs['sla_compliance_pct']}% oom={om['sla_compliance_pct']}%")
        return True

def main():
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)

    # Live mode
    if not INPUT.exists():
        print(f"No input at {INPUT}; writing empty summary.")
        records = []
    else:
        records = []
        with open(INPUT, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    result = compute_summary(records)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {OUTPUT} ({len(records)} incidents, {len(result['types'])} types)")

if __name__ == "__main__":
    main()
