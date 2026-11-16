#!/usr/bin/env python3
"""load_trend.py - regression detector for portal load baseline (goal #4).
Reads memory/ops/load-baseline.jsonl, computes rolling p95/p99 baselines per
concurrency level, flags regressions > REGRESS_PCT above the median of prior days.
Output: memory/ops/load-trend-report.json + one-line stdout verdict.

Usage: python load_trend.py [--threshold 0.30]
"""
import json, sys, os, statistics, argparse
from datetime import datetime

BASELINE_FILE = os.path.join("memory", "ops", "load-baseline.jsonl")
REPORT_FILE = os.path.join("memory", "ops", "load-trend-report.json")
REGRESS_PCT_DEFAULT = 0.30  # 30% above median = regression
MIN_DAYS = 2  # need at least 2 data points to compute a trend

def load_days():
    """Load valid entries; skip portal-down runs (all levels 100% errors)."""
    days = []
    with open(BASELINE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Skip entries where every level had total failures (portal down)
            if all(lv["errors"] == lv["n"] for lv in d["levels"]):
                continue
            days.append(d)
    return days

def analyze(days, threshold):
    """Per concurrency level: median of prior p95/p99 vs latest; flag regression."""
    by_level = {}  # {concurrency: [(ts, p50, p95, p99, errors), ...]}
    for day in days:
        ts = day["ts"]
        for lv in day["levels"]:
            n = lv["concurrency"]
            by_level.setdefault(n, []).append((ts, lv["p50_ms"], lv["p95_ms"], lv["p99_ms"], lv["errors"]))

    findings = []
    for n in sorted(by_level):
        runs = by_level[n]
        if len(runs) < MIN_DAYS:
            continue
        # Use all prior runs as baseline, latest as "today"
        prior_p95 = [r[2] for r in runs[:-1]]
        prior_p99 = [r[3] for r in runs[:-1]]
        med_p95 = statistics.median(prior_p95)
        med_p99 = statistics.median(prior_p99)
        latest = runs[-1]
        p95_ratio = latest[2] / med_p95 if med_p95 > 0 else 1.0
        p99_ratio = latest[3] / med_p99 if med_p99 > 0 else 1.0
        regressions = []
        if p95_ratio > (1 + threshold):
            regressions.append(f"p95 {latest[2]:.1f}ms vs median {med_p95:.1f}ms (+{(p95_ratio-1)*100:.0f}%)")
        if p99_ratio > (1 + threshold):
            regressions.append(f"p99 {latest[3]:.1f}ms vs median {med_p99:.1f}ms (+{(p99_ratio-1)*100:.0f}%)")
        findings.append({
            "concurrency": n,
            "days_observed": len(runs),
            "latest_ts": latest[0],
            "median_p95_ms": round(med_p95, 1),
            "median_p99_ms": round(med_p99, 1),
            "latest_p95_ms": latest[2],
            "latest_p99_ms": latest[3],
            "p95_ratio": round(p95_ratio, 3),
            "p99_ratio": round(p99_ratio, 3),
            "regression": len(regressions) > 0,
            "details": regressions
        })
    return findings

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=REGRESS_PCT_DEFAULT)
    args = ap.parse_args()

    if not os.path.exists(BASELINE_FILE):
        print("load_trend: no baseline file yet")
        return 1

    days = load_days()
    if len(days) < MIN_DAYS:
        report = {"ts": datetime.now().isoformat(), "days": len(days),
                  "status": "insufficient_data", "note": f"need >= {MIN_DAYS} days"}
        with open(REPORT_FILE, "w") as f:
            json.dump(report, f, indent=2)
        print(f"load_trend: {len(days)} day(s) - insufficient (need {MIN_DAYS})")
        return 0

    findings = analyze(days, args.threshold)
    regressions_found = [f for f in findings if f["regression"]]
    status = "REGRESSION_DETECTED" if regressions_found else "OK"
    report = {
        "ts": datetime.now().isoformat(),
        "days": len(days),
        "threshold_pct": args.threshold * 100,
        "status": status,
        "findings": findings,
        "regressions": regressions_found
    }
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    if regressions_found:
        for r in regressions_found:
            print(f"load_trend REGRESSION c={r['concurrency']}: {'; '.join(r['details'])}")
    else:
        print(f"load_trend OK ({len(days)} days, no regression > {args.threshold*100:.0f}%)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
