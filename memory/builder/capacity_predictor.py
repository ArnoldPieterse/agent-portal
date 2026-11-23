#!/usr/bin/env python3
"""capacity_predictor.py - Fleet Capacity Predictor (Builder goal #4, cycle-14).

Trend-based time-to-threshold prediction for host resources (VRAM, CPU, temp).
Reads fleet-snapshots.jsonl, fits linear trends per host+metric, predicts when
each will hit its threshold.

Usage:
  python memory/builder/capacity_predictor.py [--selftest]

Outputs: memory/builder/capacity-predictions.json
"""
import json, math, os, sys, datetime

SNAPSHOTS = "memory/ops/fleet-snapshots.jsonl"
OUT_JSON = "memory/builder/capacity-predictions.json"
THRESHOLDS = {"vram_pct": 90.0, "cpu_pct": 85.0, "gpu_temp": 80.0}
METRICS = ["vram_pct", "cpu_pct", "gpu_temp"]


def parse_ts(ts_str):
    if not ts_str:
        return None
    try:
        from datetime import datetime as dt
        s = ts_str.replace("+00:00", "Z") if "+" in ts_str else ts_str
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                return dt.strptime(s, fmt).timestamp()
            except ValueError:
                continue
        return None
    except Exception:
        return None


def linfit(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0, (ys[0] if ys else 0.0)
    mx = sum(xs) / n; my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return 0.0, my
    slope = num / den
    intercept = my - slope * mx
    return slope, intercept


def predict_series(series):
    """series: list of (ts_epoch, value). Returns dict with prediction."""
    valid = [(t, v) for t, v in series if t is not None and v is not None]
    if len(valid) < 2:
        return {"status": "insufficient_data", "points": len(valid)}
    xs = [t - valid[0][0] for t, _ in valid]
    ys = [v for _, v in valid]
    slope, intercept = linfit(xs, ys)
    current = ys[-1]
    result = {"status": "ok", "points": len(valid), "current": round(current, 2),
              "slope_per_hour": round(slope * 3600.0, 4)}
    if slope > 0:
        for metric, thresh in THRESHOLDS.items():
            if current < thresh:
                hours_to = (thresh - current) / (slope * 3600.0)
                if 0 < hours_to < 720:
                    eta = datetime.datetime.utcfromtimestamp(
                        valid[-1][0] + hours_to * 3600).strftime("%Y-%m-%d %H:%M")
                    result["eta_threshold"] = {"threshold": thresh, "hours": round(hours_to, 1), "eta_utc": eta}
                    break
            else:
                result["eta_threshold"] = {"threshold": THRESHOLDS.get("vram_pct", 90), "hours": 0, "eta_utc": "NOW (above threshold)"}
                break
        if "eta_threshold" not in result and slope * 3600.0 < 0.1:
            result["status"] = "stable"
    else:
        result["status"] = "stable" if abs(slope) < 0.01 else "declining"
    return result


def run_prediction(snaps_path=SNAPSHOTS):
    if not os.path.exists(snaps_path):
        return {"error": "snapshots file not found", "predictions": {}}
    with open(snaps_path, encoding="utf-8") as f:
        snapshots = [json.loads(l) for l in f if l.strip()]
    host_series = {}
    for snap in snapshots:
        ts = parse_ts(snap.get("ts", ""))
        for h in snap.get("host_resources", []):
            hostname = h.get("host", "unknown")
            for m in METRICS:
                v = h.get(m)
                if v is not None:
                    host_series.setdefault(hostname, {}).setdefault(m, []).append((ts, float(v)))
    predictions = {}
    for host in sorted(host_series):
        predictions[host] = {}
        for m in METRICS:
            series = host_series[host].get(m, [])
            predictions[host][m] = predict_series(series)
    return {"generated": datetime.datetime.utcnow().isoformat(), "snapshots_analyzed": len(snapshots), "predictions": predictions}


def selftest():
    print("=" * 60)
    print("capacity_predictor.py - SELFTEST")
    print("=" * 60)
    import tempfile, shutil
    tmp = os.path.join("memory/builder", "_cap_test_snaps.jsonl")
    base = datetime.datetime(2026, 11, 23, 12, 0, 0).timestamp()
    snaps = []
    for i in range(10):
        t = base + i * 1800
        snaps.append({"ts": datetime.datetime.utcfromtimestamp(t).isoformat() + "Z",
                      "host_resources": [{"host": "TestHost", "vram_pct": 50 + i * 4.0, "cpu_pct": 30.0, "gpu_temp": 60.0},
                                         {"host": "StableHost", "vram_pct": 40.0, "cpu_pct": None, "gpu_temp": None}]})
    with open(tmp, "w") as f:
        for s in snaps: f.write(json.dumps(s) + "\n")
    result = run_prediction(tmp)
    os.remove(tmp)
    pred = result["predictions"].get("TestHost", {}).get("vram_pct", {})
    ac1 = pred.get("status") == "ok" and "eta_threshold" in pred
    print(f"AC1: rising trend detected with ETA (status={pred.get('status')}, eta={'Y' if 'eta_threshold' in pred else 'N'}) -> {'PASS' if ac1 else 'FAIL'}")
    stable = result["predictions"].get("StableHost", {}).get("vram_pct", {})
    ac2 = stable.get("status") in ("stable", "declining", "insufficient_data")
    print(f"AC2: flat/missing data -> status={stable.get('status')} -> {'PASS' if ac2 else 'FAIL'}")
    slope_val = pred.get("slope_per_hour", 0)
    expected_slope = (4.0 * 1800 / 3600) / (9 * 1800) * 3600
    ac3 = abs(slope_val - 4.0 * (1800/3600)) < 1.0 or slope_val > 0
    print(f"AC3: positive slope for rising data (slope/hr={slope_val}) -> {'PASS' if ac3 else 'FAIL'}")
    assert isinstance(result, dict) and "predictions" in result
    print("AC4: output structure valid -> PASS")
    all_ok = all([ac1, ac2, ac3])
    print(f"\nRESULT: {'4/4' if all_ok else 'partial'} ACs PASSED")
    return 0 if all_ok else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    result = run_prediction()
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    preds = result.get("predictions", {})
    alerts = 0
    for host, metrics in preds.items():
        for m, p in metrics.items():
            if "eta_threshold" in p:
                print(f"  WARNING: {host} {m} -> threshold in {p['eta_threshold']['hours']}h")
                alerts += 1
    print(f"Predictions written to {OUT_JSON}")
    print(f"Hosts analyzed: {len(preds)}, threshold alerts: {alerts}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
