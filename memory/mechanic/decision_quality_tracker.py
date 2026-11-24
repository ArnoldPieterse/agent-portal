"""Decision Quality Tracker.

Reads auto-ops-decisions.jsonl and computes quality metrics:
  - positive_pct: fraction of decisions with no follow-up within 24h
  - trend: up/down/stable over recent window
  - alert: True if positive_pct < 80%

Output: memory/ops/decision-quality.json

Usage:
  python memory/mechanic/decision_quality_tracker.py           # live
  python memory/mechanic/decision_quality_tracker.py --selftest  # simulated
"""
import json, pathlib, datetime, sys

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
INPUT = BASE / "memory" / "ops" / "auto-ops-decisions.jsonl"
OUTPUT = BASE / "memory" / "ops" / "decision-quality.json"

ALERT_THRESHOLD = 0.80  # alert if <80% positive

def read_decisions(path=None):
    """Read decision records from jsonl file."""
    p = pathlib.Path(path) if path else INPUT
    if not p.exists():
        return []
    records = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records

def is_positive(record):
    """A decision is positive if no follow-up within 24h."""
    fu = record.get("follow_up_ts")
    if fu is None:
        return True
    try:
        ts = datetime.datetime.fromisoformat(record["ts"])
        fut = datetime.datetime.fromisoformat(fu)
        delta_h = (fut - ts).total_seconds() / 3600.0
        return delta_h >= 24.0
    except (KeyError, ValueError, TypeError):
        return True

def compute_quality(records):
    """Compute quality metrics from decision records."""
    if not records:
        return {
            "generated": datetime.datetime.now().isoformat(),
            "total_decisions": 0,
            "positive_pct": None,
            "trend": "insufficient_data",
            "alert": False,
            "detail": "No decision records found"
        }
    
    positives = sum(1 for r in records if is_positive(r))
    total = len(records)
    pct = positives / total
    
    trend = "stable"
    if total >= 10:
        recent = records[-5:]
        prior = records[:-5]  # all records before the last 5
        recent_pct = sum(1 for r in recent if is_positive(r)) / len(recent)
        prior_pct = sum(1 for r in prior if is_positive(r)) / len(prior)
        if recent_pct > prior_pct + 0.05:
            trend = "up"
        elif recent_pct < prior_pct - 0.05:
            trend = "down"
    elif total >= 3:
        trend = "building"
    
    return {
        "generated": datetime.datetime.now().isoformat(),
        "total_decisions": total,
        "positive_count": positives,
        "positive_pct": round(pct * 100, 1),
        "trend": trend,
        "alert": pct < ALERT_THRESHOLD,
        "alert_threshold_pct": ALERT_THRESHOLD * 100,
    }

def selftest():
    """Verify: 20 test decisions; quality correct; drop triggers alert."""
    errors = []
    base_ts = datetime.datetime(2026, 11, 24, 12, 0, 0)
    
    # Test 1: 20 decisions, 18 positive (90%) -> no alert
    records = []
    for i in range(20):
        ts = (base_ts + datetime.timedelta(hours=i)).isoformat()
        if i < 18:
            records.append({"ts": ts, "action": f"auto-fix-{i}", "follow_up_ts": None})
        else:
            fut = (base_ts + datetime.timedelta(hours=i) + datetime.timedelta(hours=2)).isoformat()
            records.append({"ts": ts, "action": f"auto-fix-{i}", "follow_up_ts": fut})
    result = compute_quality(records)
    if result["total_decisions"] != 20:
        errors.append(f"Expected 20 decisions, got {result['total_decisions']}")
    if result["positive_pct"] != 90.0:
        errors.append(f"Expected 90.0% positive, got {result['positive_pct']}")
    if result["alert"] is not False:
        errors.append(f"90% should not alert, but alert={result['alert']}")
    
    # Test 2: 10 decisions, 7 positive (70%) -> alert fires
    records_bad = []
    for i in range(10):
        ts = (base_ts + datetime.timedelta(hours=i)).isoformat()
        if i < 7:
            records_bad.append({"ts": ts, "action": f"fix-{i}", "follow_up_ts": None})
        else:
            fut = (base_ts + datetime.timedelta(hours=i) + datetime.timedelta(hours=1)).isoformat()
            records_bad.append({"ts": ts, "action": f"fix-{i}", "follow_up_ts": fut})
    result_bad = compute_quality(records_bad)
    if result_bad["positive_pct"] != 70.0:
        errors.append(f"Expected 70.0%, got {result_bad['positive_pct']}")
    if result_bad["alert"] is not True:
        errors.append(f"70% should alert, but alert={result_bad['alert']}")
    
    # Test 3: trend down (first 10 positive, last 10 negative)
    records_trend = []
    for i in range(20):
        ts = (base_ts + datetime.timedelta(hours=i)).isoformat()
        if i < 10:
            records_trend.append({"ts": ts, "action": f"ok-{i}", "follow_up_ts": None})
        else:
            fut = (base_ts + datetime.timedelta(hours=i) + datetime.timedelta(minutes=30)).isoformat()
            records_trend.append({"ts": ts, "action": f"bad-{i}", "follow_up_ts": fut})
    result_trend = compute_quality(records_trend)
    if result_trend["trend"] != "down":
        errors.append(f"Expected trend=down, got {result_trend['trend']}")
    
    # Test 4: empty -> insufficient_data
    result_empty = compute_quality([])
    if result_empty["trend"] != "insufficient_data":
        errors.append(f"Expected insufficient_data, got {result_empty['trend']}")
    
    # Test 5: follow-up at exactly 24h -> positive (boundary)
    records_boundary = [{
        "ts": base_ts.isoformat(),
        "action": "boundary-test",
        "follow_up_ts": (base_ts + datetime.timedelta(hours=24)).isoformat()
    }]
    r = compute_quality(records_boundary)
    if r["positive_pct"] != 100.0:
        errors.append(f"24h follow-up should be positive, got {r['positive_pct']}%")
    
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return False
    else:
        print("PASS: all 5 selftest checks OK")
        print(f"  20 decisions -> 90% positive, no alert")
        print(f"  10 decisions -> 70% positive, alert=True")
        print(f"  trend down detected correctly")
        print(f"  empty -> insufficient_data")
        print(f"  24h boundary -> positive")
        return True

def main():
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    
    records = read_decisions()
    result = compute_quality(records)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {OUTPUT}: total={result['total_decisions']}, positive_pct={result.get('positive_pct')}, alert={result['alert']}")

if __name__ == "__main__":
    main()