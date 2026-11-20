#!/usr/bin/env python3
"""
capacity_trend.py (2026-11-20, Mechanic goal #9)
Linear-trend prediction for fleet resource exhaustion.

Reads from memory/mechanic/capacity_data.jsonl (one JSON object per line).
Each record: {"ts": "ISO8601", "host": "White|Pale|Black|Red", "metric": "vram_gb|disk_pct|...", "value": <float>}

Usage:
  python memory/mechanic/capacity_trend.py --append --host White --metric vram_gb --value 24.5
  python memory/mechanic/capacity_trend.py --report [--threshold 90]
  python memory/mechanic/capacity_trend.py --selftest
"""
import json, os, sys, argparse, datetime

DATA_FILE = "memory/mechanic/capacity_data.jsonl"
THRESHOLD_DEFAULT = 90.0  # percent (for disk_pct) or GB (for vram_gb, use total as reference)

def read_records():
    if not os.path.exists(DATA_FILE):
        return []
    records = []
    with open(DATA_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                records.append(rec)
            except json.JSONDecodeError:
                continue
    return records

def append_record(host, metric, value, ts=None):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    rec = {
        "ts": ts or datetime.datetime.now().isoformat(),
        "host": host,
        "metric": metric,
        "value": value
    }
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec

def linear_trend(points):
    """Simple least-squares linear fit. points = [(x, y)] where x is days since first point.
    Returns (slope_per_day, intercept, r_squared)."""
    n = len(points)
    if n < 2:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    ss_xy = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    ss_xx = sum((x - x_mean) ** 2 for x in xs)
    if ss_xx == 0:
        return None
    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean
    # R-squared
    ss_yy = sum((y - y_mean) ** 2 for y in ys)
    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy > 0 else 1.0
    return (slope, intercept, r_squared)

def predict_days_to_threshold(slope_per_day, current_value, threshold):
    """Days until value reaches threshold. None if not growing or already above."""
    if slope_per_day <= 0:
        return None  # not growing
    if current_value >= threshold:
        return 0  # already breached
    remaining = threshold - current_value
    days = remaining / slope_per_day
    return days

def generate_report(threshold=THRESHOLD_DEFAULT):
    records = read_records()
    if not records:
        return {"status": "no_data", "message": f"No records in {DATA_FILE}"}
    
    # Group by (host, metric)
    groups = {}
    for rec in records:
        key = (rec["host"], rec["metric"])
        if key not in groups:
            groups[key] = []
        groups[key].append(rec)
    
    report = {
        "generated": datetime.datetime.now().isoformat(),
        "total_records": len(records),
        "hosts": sorted(set(r["host"] for r in records)),
        "metrics": sorted(set(r["metric"] for r in records)),
        "predictions": []
    }
    
    now = datetime.datetime.now()
    for (host, metric), recs in sorted(groups.items()):
        if len(recs) < 2:
            report["predictions"].append({
                "host": host, "metric": metric,
                "status": "insufficient_data", "n": len(recs)
            })
            continue
        
        # Sort by timestamp
        recs.sort(key=lambda r: r["ts"])
        first_ts = datetime.datetime.fromisoformat(recs[0]["ts"])
        
        # Build points: (days_since_first, value)
        points = []
        for r in recs:
            ts = datetime.datetime.fromisoformat(r["ts"])
            days = (ts - first_ts).total_seconds() / 86400.0
            points.append((days, r["value"]))
        
        trend = linear_trend(points)
        if trend is None:
            report["predictions"].append({
                "host": host, "metric": metric,
                "status": "trend_undetermined", "n": len(recs)
            })
            continue
        
        slope, intercept, r2 = trend
        current = recs[-1]["value"]
        days_to_threshold = predict_days_to_threshold(slope, current, threshold)
        
        pred = {
            "host": host, "metric": metric,
            "n": len(recs),
            "current": current,
            "slope_per_day": round(slope, 4),
            "r_squared": round(r2, 3),
            "threshold": threshold,
        }
        
        if days_to_threshold is None:
            pred["status"] = "stable_or_declining"
        elif days_to_threshold == 0:
            pred["status"] = "BREACHED"
            pred["alert"] = f"{host} {metric} already at/above {threshold}"
        elif days_to_threshold < 48 / 24.0:  # < 48 hours
            pred["status"] = "ALERT_IMMINENT"
            pred["days_to_breach"] = round(days_to_threshold, 1)
            pred["alert"] = f"{host} {metric} predicted to breach {threshold} in {days_to_threshold:.1f} days"
        else:
            pred["status"] = "ok"
            pred["days_to_breach"] = round(days_to_threshold, 1)
        
        report["predictions"].append(pred)
    
    return report

def selftest():
    """Self-test with synthetic data."""
    import tempfile
    results = []
    
    # Test 1: linear growth hits threshold
    test_file = "memory/mechanic/_selftest_capacity.jsonl"
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    base_ts = datetime.datetime(2026, 11, 1)
    with open(test_file, "w") as f:
        for i in range(10):
            ts = (base_ts + datetime.timedelta(days=i)).isoformat()
            rec = {"ts": ts, "host": "Test", "metric": "disk_pct", "value": 50 + i * 4.0}
            f.write(json.dumps(rec) + "\n")
    
    # Read and compute
    records = []
    with open(test_file) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    points = []
    first_ts = datetime.datetime.fromisoformat(records[0]["ts"])
    for r in records:
        ts = datetime.datetime.fromisoformat(r["ts"])
        days = (ts - first_ts).total_seconds() / 86400.0
        points.append((days, r["value"]))
    
    trend = linear_trend(points)
    assert trend is not None, "T1: trend should be computed"
    slope, intercept, r2 = trend
    # Expected: slope = 4 per day (50 + i*4 over 9 days span)
    assert abs(slope - 4.0) < 0.1, f"T1: slope should be ~4, got {slope}"
    assert r2 > 0.99, f"T1: r2 should be >0.99 for perfect line, got {r2}"
    
    # Predict: current=86, threshold=90, slope=4 -> (90-86)/4 = 1 day
    days = predict_days_to_threshold(slope, 86.0, 90.0)
    assert abs(days - 1.0) < 0.1, f"T1: expected ~1 day, got {days}"
    results.append("T1 PASS: linear trend + prediction correct")
    
    # Test 2: stable (no growth) -> None
    days = predict_days_to_threshold(0.0, 50.0, 90.0)
    assert days is None, "T2: flat line should return None"
    results.append("T2 PASS: stable metric returns None")
    
    # Test 3: already breached -> 0
    days = predict_days_to_threshold(1.0, 95.0, 90.0)
    assert days == 0, "T3: already above threshold should return 0"
    results.append("T3 PASS: breached returns 0")
    
    # Test 4: declining -> None
    days = predict_days_to_threshold(-1.0, 50.0, 90.0)
    assert days is None, "T4: declining should return None"
    results.append("T4 PASS: declining returns None")
    
    # Test 5: insufficient data
    trend = linear_trend([(0, 50)])
    assert trend is None, "T5: single point should return None"
    results.append("T5 PASS: single point returns None")
    
    # Cleanup
    os.remove(test_file)
    
    print(f"capacity_trend selftest: {len(results)}/5 PASS")
    for r in results:
        print(f"  {r}")
    return True

def main():
    ap = argparse.ArgumentParser(description="Fleet capacity trend prediction")
    ap.add_argument("--append", action="store_true", help="Append a data point")
    ap.add_argument("--host", required=False, help="Host name (for --append)")
    ap.add_argument("--metric", required=False, help="Metric name (for --append)")
    ap.add_argument("--value", type=float, required=False, help="Value (for --append)")
    ap.add_argument("--report", action="store_true", help="Generate prediction report")
    ap.add_argument("--threshold", type=float, default=THRESHOLD_DEFAULT)
    ap.add_argument("--selftest", action="store_true", help="Run self-test")
    args = ap.parse_args()
    
    if args.selftest:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif args.append:
        if not all([args.host, args.metric, args.value is not None]):
            print("ERROR: --append requires --host, --metric, --value", file=sys.stderr)
            sys.exit(1)
        rec = append_record(args.host, args.metric, args.value)
        print(f"Appended: {json.dumps(rec)}")
    elif args.report:
        report = generate_report(args.threshold)
        print(json.dumps(report, indent=2))
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
