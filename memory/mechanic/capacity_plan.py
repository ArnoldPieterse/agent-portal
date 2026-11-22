#!/usr/bin/env python3
"""capacity_plan.py - Fleet capacity planning: trend + breach prediction.
Goal #9: Capacity Planning Dashboard

Reads host_metrics.jsonl (or --input), computes linear regression per metric,
predicts when 90% threshold will be breached, alerts 48h before.

Usage:
    python memory/mechanic/capacity_plan.py [--input FILE] [--threshold 90] [--alert-hours 48] [--json]

Outputs: memory/mechanic/capacity-plan-YYYY-MM-DD.md (report) + capacity-plan-latest.json
Exit codes: 0=OK, 1=insufficient data (<3 points), 2=breach predicted within alert window
"""
import json, os, sys, math, datetime, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT = os.path.join(HERE, "..", "ops", "host_metrics.jsonl")
REPORT_DIR = HERE
THRESHOLD_PCT = 90.0
ALERT_HOURS = 48


def linear_regression(points):
    """points: list of (x, y) where x is epoch seconds. Returns (slope_per_day, intercept)."""
    n = len(points)
    if n < 2:
        return None, None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    den = sum((xs[i] - mean_x) ** 2 for i in range(n))
    if den == 0:
        return None, None
    slope = num / den  # per second
    intercept = mean_y - slope * mean_x
    return slope * 86400, intercept  # convert to per-day


def predict_breach(slope_per_day, current_val, threshold):
    """Given slope (pct/day) and current value, return days until breach (None if not trending up)."""
    if slope_per_day is None or slope_per_day <= 0:
        return None
    remaining = threshold - current_val
    if remaining <= 0:
        return 0  # already breached
    return remaining / slope_per_day


def parse_ts(ts_str):
    """Parse various timestamp formats to epoch seconds."""
    try:
        dt = datetime.datetime.fromisoformat(ts_str)
        return dt.timestamp()
    except (ValueError, TypeError):
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.datetime.strptime(ts_str[:19], fmt).timestamp()
        except ValueError:
            continue
    return None


def collect_metrics(input_path):
    """Read JSONL and group by host+metric. Returns {host: {metric: [(epoch, value)]}}."""
    data = {}
    if not os.path.exists(input_path):
        return data
    with open(input_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            host = entry.get("host", "unknown").lower()
            ts_raw = entry.get("ts", "")
            epoch = parse_ts(ts_raw) if isinstance(ts_raw, str) else (ts_raw if isinstance(ts_raw, (int, float)) else None)
            if epoch is None:
                continue
            
            # Extract metrics
            disk = entry.get("disk", {})
            mem = entry.get("mem", {})
            
            if "pct_used" in disk:
                data.setdefault(host, {}).setdefault("disk_pct", []).append((epoch, float(disk["pct_used"])))
            if "pct_used" in mem:
                data.setdefault(host, {}).setdefault("mem_pct", []).append((epoch, float(mem["pct_used"])))
            
            # VRAM if present
            vram = entry.get("vram", {})
            if "pct_used" in vram:
                data.setdefault(host, {}).setdefault("vram_pct", []).append((epoch, float(vram["pct_used"])))
    
    # Sort each series by time
    for host in data:
        for metric in data[host]:
            data[host][metric].sort(key=lambda p: p[0])
    return data


def analyze(data, threshold=THRESHOLD_PCT, alert_hours=ALERT_HOURS):
    """Run trend analysis. Returns list of result dicts."""
    results = []
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    
    for host in sorted(data.keys()):
        for metric in sorted(data[host].keys()):
            points = data[host][metric]
            n = len(points)
            
            if n < 3:
                results.append({
                    "host": host, "metric": metric, "n_points": n,
                    "status": "INSUFFICIENT_DATA", "slope_per_day": None,
                    "current": points[-1][1] if points else None,
                    "days_to_breach": None, "alert": False
                })
                continue
            
            slope, intercept = linear_regression(points)
            current = points[-1][1]
            days_to_breach = predict_breach(slope, current, threshold)
            
            alert = False
            if days_to_breach is not None and days_to_breach * 24 <= alert_hours:
                alert = True
            
            results.append({
                "host": host, "metric": metric, "n_points": n,
                "status": "OK", "slope_per_day": round(slope, 4) if slope else None,
                "current": round(current, 2),
                "days_to_breach": round(days_to_breach, 1) if days_to_breach is not None else None,
                "alert": alert,
                "threshold_pct": threshold
            })
    return results


def write_report(results, output_path):
    """Write markdown report."""
    lines = [
        f"# Fleet Capacity Plan - {datetime.datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"Threshold: {THRESHOLD_PCT}% | Alert window: {ALERT_HOURS}h",
        "",
        "| Host | Metric | Points | Current % | Trend (%/day) | Days to 90% | Alert |",
        "|------|--------|--------|-----------|----------------|-------------|-------|",
    ]
    for r in results:
        slope_s = f"{r['slope_per_day']:+.3f}" if r['slope_per_day'] is not None else "-"
        breach_s = f"{r['days_to_breach']:.1f}d" if r['days_to_breach'] is not None else "stable"
        alert_s = "**YES**" if r['alert'] else "no"
        status_note = " (insufficient)" if r['status'] == 'INSUFFICIENT_DATA' else ""
        lines.append(f"| {r['host']} | {r['metric']}{status_note} | {r['n_points']} | {r['current']} | {slope_s} | {breach_s} | {alert_s} |")
    
    # Recommendations
    lines.append("")
    lines.append("## Recommendations")
    alerts = [r for r in results if r['alert']]
    if alerts:
        for a in alerts:
            lines.append(f"- **ALERT**: {a['host']} {a['metric']} predicted to breach 90% in {a['days_to_breach']} days")
    else:
        stable = [r for r in results if r['status'] == 'OK' and (r['days_to_breach'] is None or r['days_to_breach'] > 30)]
        insufficient = [r for r in results if r['status'] == 'INSUFFICIENT_DATA']
        if stable:
            lines.append("- All tracked metrics trending stable or well below threshold (>30 days to breach).")
        if insufficient:
            lines.append(f"- {len(insufficient)} metric(s) have <3 data points. Register daily probe schtask to accumulate history.")
    
    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Fleet capacity planning")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input JSONL file")
    parser.add_argument("--threshold", type=float, default=THRESHOLD_PCT, help="Breach threshold %%")
    parser.add_argument("--alert-hours", type=int, default=ALERT_HOURS, help="Alert window in hours")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of markdown")
    args = parser.parse_args()
    
    data = collect_metrics(args.input)
    if not data:
        print(f"FAIL: no data found at {args.input}")
        return 1
    
    results = analyze(data, threshold=args.threshold, alert_hours=args.alert_hours)
    
    # Write outputs
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(REPORT_DIR, f"capacity-plan-{date_str}.md")
    json_path = os.path.join(REPORT_DIR, "capacity-plan-latest.json")
    
    write_report(results, report_path)
    with open(json_path, "w") as f:
        json.dump({"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "results": results}, f, indent=2)
    
    # Print summary
    alerts = [r for r in results if r['alert']]
    print(f"PASS: {len(results)} metrics analyzed, {len(alerts)} alert(s)")
    print(f"Report: {os.path.relpath(report_path)}")
    print(f"JSON:   {os.path.relpath(json_path)}")
    
    if alerts:
        for a in alerts:
            print(f"  ALERT: {a['host']}/{a['metric']} breach in {a['days_to_breach']}d")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
