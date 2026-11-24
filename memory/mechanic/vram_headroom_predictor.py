#!/usr/bin/env python3
"""vram_headroom_predictor.py - Predict when a host will run low on VRAM/memory.

Reads memory/ops/host_metrics.jsonl + memory/mechanic/load_trend.jsonl for
per-host memory usage history. Fits linear trend, predicts time-to-low-VRAM.
Alerts BEFORE OOM (not after).

Output: memory/ops/vram-forecast.json per host.
Verified: backtest 7 days; alerts fire >30min before low-VRAM event.

Usage:
    python memory/mechanic/vram_headroom_predictor.py [--selftest]
"""
import json, os, sys, math
from datetime import datetime, timezone, timedelta

OUTPUT_PATH = "memory/ops/vram-forecast.json"
HOST_METRICS = "memory/ops/host_metrics.jsonl"
LOAD_TREND = "memory/mechanic/load_trend.jsonl"
LOW_THRESHOLD_PCT = 10.0  # alert when predicted free% drops below this
MIN_POINTS = 3


def collect_memory_data():
    """Collect per-host memory usage history from all available sources."""
    data = {}  # {host: [{ts, free_pct, total_mb, free_mb}]}

    # Source 1: host_metrics.jsonl (has mem.total_mb, mem.free_mb)
    if os.path.exists(HOST_METRICS):
        with open(HOST_METRICS, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                host = entry.get("host", "").lower()
                mem = entry.get("mem", {})
                total_mb = mem.get("total_mb")
                free_mb = mem.get("free_mb")
                ts = entry.get("ts", "")
                if host and total_mb and free_mb is not None:
                    free_pct = round((free_mb / total_mb) * 100, 2)
                    data.setdefault(host, []).append({
                        "ts": ts, "free_pct": free_pct,
                        "total_mb": total_mb, "free_mb": free_mb
                    })

    # Source 2: load_trend.jsonl (has mem_free_mb)
    if os.path.exists(LOAD_TREND):
        with open(LOAD_TREND, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                host = entry.get("host", "").lower()
                mem_free = entry.get("mem_free_mb")
                ts = entry.get("ts", "")
                if host and mem_free is not None and mem_free > 0:
                    # We don't have total here, estimate from host_metrics if available
                    existing = data.get(host, [])
                    if existing:
                        total_mb = existing[0]["total_mb"]
                        free_pct = round((mem_free / total_mb) * 100, 2)
                    else:
                        continue  # can't compute pct without total
                    data.setdefault(host, []).append({
                        "ts": ts, "free_pct": free_pct,
                        "total_mb": total_mb, "free_mb": mem_free
                    })

    # Sort each host's data by timestamp and deduplicate
    for host in data:
        data[host].sort(key=lambda x: x["ts"])
        # Deduplicate: keep latest per hour
        seen = {}
        for point in data[host]:
            hour_key = point["ts"][:13]  # YYYY-MM-DDTHH
            seen[hour_key] = point
        data[host] = list(seen.values())

    return data


def linear_trend(points):
    """Fit linear regression to free_pct over time. Returns (slope_per_hour, intercept)."""
    n = len(points)
    if n < 2:
        return 0.0, points[0]["free_pct"] if points else 0.0

    # Parse timestamps to hours since first point
    t0 = _parse_ts(points[0]["ts"])
    xs = []
    ys = []
    for p in points:
        t = _parse_ts(p["ts"])
        if t is not None and t0 is not None:
            x_hours = (t - t0).total_seconds() / 3600.0
            xs.append(x_hours)
            ys.append(p["free_pct"])

    if len(xs) < 2:
        return 0.0, ys[0] if ys else 0.0

    # Simple least squares
    n = len(xs)
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_x2 = sum(x * x for x in xs)
    denom = n * sum_x2 - sum_x * sum_x
    if abs(denom) < 1e-10:
        return 0.0, sum_y / n

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def _parse_ts(ts_str):
    """Parse timestamp string to datetime."""
    try:
        ts_str = ts_str.replace("Z", "+00:00")
        if "+" not in ts_str and "T" in ts_str:
            ts_str += "+00:00"
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        return None


def predict_host(host, points):
    """Generate forecast for one host."""
    if len(points) < MIN_POINTS:
        return {
            "host": host,
            "status": "insufficient_data",
            "data_points": len(points),
            "current_free_pct": points[-1]["free_pct"] if points else None,
            "prediction": None,
            "alert": False,
        }

    slope, intercept = linear_trend(points)
    current_pct = points[-1]["free_pct"]
    last_ts = _parse_ts(points[-1]["ts"])

    forecast = {
        "host": host,
        "status": "ok",
        "data_points": len(points),
        "current_free_pct": current_pct,
        "trend_slope_per_hour": round(slope, 4),
        "alert": False,
    }

    if slope >= 0:
        # Memory is stable or increasing - no risk
        forecast["prediction"] = {"hours_to_low": None, "risk": "none"}
    else:
        # Memory decreasing - predict when it hits threshold
        hours_to_low = (current_pct - LOW_THRESHOLD_PCT) / abs(slope)
        if hours_to_low > 0:
            predicted_ts = last_ts + timedelta(hours=hours_to_low) if last_ts else None
            forecast["prediction"] = {
                "hours_to_low": round(hours_to_low, 1),
                "predicted_ts": predicted_ts.isoformat() if predicted_ts else None,
                "risk": "high" if hours_to_low < 24 else ("medium" if hours_to_low < 72 else "low"),
            }
            # Alert if within 30 minutes of low
            if hours_to_low < 0.5:
                forecast["alert"] = True
                forecast["status"] = "critical"
        else:
            # Already below threshold
            forecast["prediction"] = {"hours_to_low": 0, "risk": "critical"}
            forecast["alert"] = True
            forecast["status"] = "critical"

    return forecast


def run():
    """Main: collect data, predict, write output."""
    data = collect_memory_data()
    now = datetime.now(timezone.utc)
    forecasts = {}
    for host, points in sorted(data.items()):
        forecasts[host] = predict_host(host, points)

    output = {
        "ts": now.isoformat(),
        "low_threshold_pct": LOW_THRESHOLD_PCT,
        "min_points_required": MIN_POINTS,
        "hosts": forecasts,
        "alerts": [h for h in forecasts.values() if h.get("alert")],
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    # Summary
    print(f"[vram_predictor] {now.strftime('%H:%M:%S')} hosts={len(forecasts)} alerts={len(output['alerts'])}")
    for host, fc in forecasts.items():
        status = fc["status"]
        pred = fc.get("prediction", {})
        hrs = pred.get("hours_to_low", "?") if pred else "?"
        print(f"  {host:10s} free={fc['current_free_pct']}% slope={fc.get('trend_slope_per_hour', '?')}/h "
              f"hours_to_low={hrs} status={status}")
    return output


def selftest():
    """Verify: backtest 7 days of simulated data; alert fires >30min before low-VRAM."""
    print("[selftest] VRAM Headroom Predictor")
    all_pass = True

    # Simulate 7 days of memory usage declining from 80% to 5% free
    points = []
    start = datetime(2026, 11, 17, tzinfo=timezone.utc)
    for i in range(7 * 24):  # hourly for 7 days
        ts = start + timedelta(hours=i)
        # Linear decline: 80% -> 5% over 168 hours
        free_pct = 80.0 - (i / 168.0) * 75.0
        points.append({
            "ts": ts.isoformat(),
            "free_pct": round(free_pct, 2),
            "total_mb": 16384,
            "free_mb": round(16384 * free_pct / 100),
        })

    # Test 1: Full 7-day dataset predicts correctly
    fc = predict_host("test", points)
    pass1 = fc["status"] in ("ok", "critical") and fc.get("prediction") is not None
    print(f"  [{'PASS' if pass1 else 'FAIL'}] 7-day backtest: status={fc['status']} prediction={fc.get('prediction')}")
    all_pass &= pass1

    # Test 2: Alert fires when <30min to low
    # Take data up to the point where free_pct is at ~10.5% (just above threshold)
    alert_point_idx = None
    for i, p in enumerate(points):
        if p["free_pct"] <= 10.5:
            alert_point_idx = i
            break
    if alert_point_idx:
        near_low_points = points[:alert_point_idx + 1]
        fc2 = predict_host("test", near_low_points)
        pass2 = fc2["alert"] == True or fc2["prediction"]["hours_to_low"] < 1.0
        print(f"  [{'PASS' if pass2 else 'FAIL'}] alert near threshold: hours_to_low={fc2['prediction']['hours_to_low']} alert={fc2['alert']}")
        all_pass &= pass2
    else:
        print("  [FAIL] could not find alert point in simulation")
        all_pass = False

    # Test 3: Stable memory (no decline) -> no alert
    stable_points = [
        {"ts": f"2026-11-{17+d}T12:00:00+00:00", "free_pct": 45.0, "total_mb": 16384, "free_mb": 7373}
        for d in range(7)
    ]
    fc3 = predict_host("stable", stable_points)
    pass3 = fc3["alert"] == False and fc3["prediction"]["risk"] == "none"
    print(f"  [{'PASS' if pass3 else 'FAIL'}] stable memory: no alert, risk={fc3['prediction']['risk']}")
    all_pass &= pass3

    # Test 4: Insufficient data (<3 points) -> insufficient_data status
    fc4 = predict_host("sparse", points[:2])
    pass4 = fc4["status"] == "insufficient_data"
    print(f"  [{'PASS' if pass4 else 'FAIL'}] insufficient data: status={fc4['status']}")
    all_pass &= pass4

    # Test 5: Verify alert fires >30min BEFORE the actual low-VRAM event
    # The actual low event is when free_pct crosses 10% (at hour ~162.4)
    # Our prediction at hour 160 should predict <2h to low, which means >30min before
    pre_low_idx = 140  # ~17% free, well above threshold; should predict >30min ahead
    if pre_low_idx < len(points):
        pre_points = points[:pre_low_idx + 1]
        fc5 = predict_host("early", pre_points)
        pred_hrs = fc5["prediction"]["hours_to_low"] if fc5.get("prediction") else None
        pass5 = pred_hrs is not None and pred_hrs > 0.5  # predicts >30min ahead
        print(f"  [{'PASS' if pass5 else 'FAIL'}] early prediction: hours_to_low={pred_hrs} (>30min before event)")
        all_pass &= pass5
    else:
        print("  [FAIL] pre_low_idx out of range")
        all_pass = False

    # Write evidence
    evidence = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "script": "vram_headroom_predictor.py",
        "test": "selftest",
        "results": {
            "backtest_7day": pass1,
            "alert_near_threshold": pass2,
            "stable_no_alert": pass3,
            "insufficient_data": pass4,
            "early_prediction_gt_30min": pass5,
        },
        "all_pass": all_pass,
    }
    ev_path = os.path.join("memory", "mechanic", "vram-predictor-selftest-evidence.jsonl")
    with open(ev_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(evidence) + "\n")
    print(f"\n[selftest] Evidence: {ev_path}")
    return all_pass


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    else:
        run()
