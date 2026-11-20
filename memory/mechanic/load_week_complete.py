#!/usr/bin/env python3
"""load_week_complete.py: closure verdict for Goal #1 (Portal Load Test 7-Day).

Reads memory/ops/load-baseline.jsonl, computes per-day + aggregate metrics,
and writes a PASS/FAIL report to memory/mechanic/load-test-week.md.

Usage:
    python memory/mechanic/load_week_complete.py            # full verdict (exits 0=PASS, 1=FAIL, 2=insufficient)
    python memory/mechanic/load_week_complete.py --status   # progress only, no verdict gate
"""
import json, os, sys
from datetime import datetime
from collections import defaultdict
from statistics import median

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "..", "ops", "load-baseline.jsonl")
REPORT   = os.path.join(HERE, "load-test-week.md")

# PASS thresholds (p95_ms max per concurrency level)
THRESHOLDS = {10: 200, 50: 800, 200: 3600}

def load_entries():
    entries = []
    with open(BASELINE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "levels" not in obj:
                continue
            entries.append(obj)
    return entries

def distinct_days(entries):
    days = set()
    for e in entries:
        days.add(e["ts"][:10])
    return sorted(days)

def aggregate_by_level(entries):
    agg = defaultdict(lambda: {"p50": [], "p95": [], "p99": [], "errors": 0})
    for e in entries:
        for lvl in e.get("levels", []):
            c = lvl["concurrency"]
            agg[c]["p50"].append(lvl["p50_ms"])
            agg[c]["p95"].append(lvl["p95_ms"])
            agg[c]["p99"].append(lvl["p99_ms"])
            agg[c]["errors"] += lvl.get("errors", 0)
    return agg

def verdict(agg, days):
    if len(days) < 7:
        return None, "INSUFFICIENT_DATA (%d/7 days)" % len(days)
    failures = []
    for c in sorted(THRESHOLDS.keys()):
        if c not in agg:
            continue
        p95_max = max(agg[c]["p95"])
        err_total = agg[c]["errors"]
        threshold = THRESHOLDS[c]
        if p95_max > threshold:
            failures.append("c=%d: p95_max=%.1fms > %dms" % (c, p95_max, threshold))
        if err_total > 0:
            failures.append("c=%d: %d errors across all runs" % (c, err_total))
    if failures:
        return "FAIL", "; ".join(failures)
    return "PASS", "all p95 within thresholds, zero errors"

def write_report(days, agg, verdict_str, reason, status_only=False):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Portal Load Test - 7-Day Completion Report",
        "",
        "Generated: " + now,
        "Data source: memory/ops/load-baseline.jsonl",
        "",
        "## Progress: %d/7 days" % len(days),
        "",
    ]
    if status_only or verdict_str is None:
        lines.append("**Status: IN PROGRESS** - need %d more day(s)." % max(0, 7 - len(days)))
        lines.append("")
        lines.append("Days with data: " + ", ".join(days))
        lines.append("")
    else:
        lines.append("**Verdict: %s** - %s" % (verdict_str, reason))
        lines.append("")

    # Per-day table
    day_data = defaultdict(list)
    for e in load_entries():
        day_data[e["ts"][:10]].append(e)

    lines.extend([
        "## Daily Summary",
        "",
        "| Day | Runs | c=10 p50/p95 (ms) | c=50 p50/p95 (ms) | c=200 p50/p95 (ms) | Errs |",
        "|-----|------|-------------------|-------------------|--------------------|------|",
    ])
    for day in sorted(day_data.keys()):
        entries = day_data[day]
        n = len(entries)
        last = entries[-1]
        lvls = {l["concurrency"]: l for l in last.get("levels", [])}
        c10, c50, c200 = lvls.get(10, {}), lvls.get(50, {}), lvls.get(200, {})
        errs = sum(l.get("errors", 0) for l in last.get("levels", []))
        lines.append("| %s | %d | %.1f/%.1f | %.1f/%.1f | %.1f/%.1f | %d |" % (
            day, n,
            c10.get('p50_ms', 0), c10.get('p95_ms', 0),
            c50.get('p50_ms', 0), c50.get('p95_ms', 0),
            c200.get('p50_ms', 0), c200.get('p95_ms', 0),
            errs))

    lines.extend(["", "## Aggregate (all entries)", "",
        "| Conc | n | p50 med | p95 med | p95 max | p99 max | Errs |",
        "|------|---|---------|---------|---------|---------|------|"])
    for c in sorted(agg.keys()):
        a = agg[c]
        lines.append("| %d | %d | %.1f | %.1f | %.1f | %.1f | %d |" % (
            c, len(a['p50']), median(a['p50']), median(a['p95']),
            max(a['p95']), max(a['p99']), a['errors']))

    lines.extend(["", "## Pass Thresholds", ""])
    for c, t in sorted(THRESHOLDS.items()):
        lines.append("- c=%d: p95 <= %dms" % (c, t))
    lines.append("- Zero errors at all levels")
    lines.append("")

    with open(REPORT, "w") as f:
        f.write("\n".join(lines) + "\n")

def main():
    status_only = "--status" in sys.argv
    entries = load_entries()
    days = distinct_days(entries)
    agg = aggregate_by_level(entries)
    
    if status_only or len(days) < 7:
        v, reason = None, "INSUFFICIENT_DATA (%d/7 days)" % len(days)
        write_report(days, agg, v, reason, status_only=True)
        print("[load_week_complete] %d/7 days. Need %d more." % (len(days), max(0, 7-len(days))))
        print("[load_week_complete] Report: memory/mechanic/load-test-week.md")
        sys.exit(2)
    else:
        v, reason = verdict(agg, days)
        write_report(days, agg, v, reason)
        print("[load_week_complete] VERDICT=%s - %s" % (v, reason))
        print("[load_week_complete] Report: memory/mechanic/load-test-week.md")
        sys.exit(0 if v == "PASS" else 1)

if __name__ == "__main__":
    main()
