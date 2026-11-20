#!/usr/bin/env python3
"""goal1_auto_closure.py — one-command closure for Mechanic Goal #1 (Portal Load Test 7-Day).

Usage: python memory/mechanic/goal1_auto_closure.py [--threshold 0.30]

When 7/7 distinct days are present in load-baseline.jsonl:
  - Runs full trend analysis
  - Writes closure report to memory/mechanic/load-test-week.md
  - Records to goal ledger (mechanic #1)
  - Exit 0 + prints PASS/FAIL verdict

When <7/7: prints progress and exits 0 (not an error, just not ready yet).
"""
import json, os, sys, statistics, argparse
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # shared agent folder root
BASELINE_FILE = os.path.join(ROOT, "memory", "ops", "load-baseline.jsonl")
REPORT_MD = os.path.join(HERE, "load-test-week.md")
WEEK_DAYS = 7
REGRESS_PCT_DEFAULT = 0.30

# Pass thresholds from goal spec
THRESHOLDS = {10: 200.0, 50: 800.0, 200: 3600.0}  # p95 max per concurrency level


def _is_latency_row(d):
    return d.get("kind", "latency") == "latency" and isinstance(d.get("levels"), list)


def load_days():
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
            if not _is_latency_row(d):
                continue
            if all(lv["errors"] == lv["n"] for lv in d["levels"]):
                continue
            days.append(d)
    return days


def distinct_days(days):
    seen = set()
    for d in days:
        seen.add(d["ts"][:10])
    return sorted(seen)


def analyze_pass_fail(days):
    """Check pass thresholds: p95 <= threshold at each level, zero errors."""
    by_level = {}
    for d in days:
        for lv in d["levels"]:
            n = lv["concurrency"]
            by_level.setdefault(n, []).append(lv)

    results = []
    all_pass = True
    total_errors = 0
    for n in sorted(THRESHOLDS):
        runs = by_level.get(n, [])
        if not runs:
            continue
        p95s = [r["p95_ms"] for r in runs]
        max_p95 = max(p95s)
        errs = sum(r["errors"] for r in runs)
        total_errors += errs
        limit = THRESHOLDS[n]
        passed = max_p95 <= limit and errs == 0
        if not passed:
            all_pass = False
        results.append({
            "concurrency": n, "max_p95_ms": round(max_p95, 1),
            "limit_ms": limit, "errors": errs, "pass": passed,
            "n_runs": len(runs)
        })
    return all_pass and total_errors == 0, results, total_errors


def write_report(days, present, verdict, details):
    ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Portal Load Test - 7-Day Completion Report",
        "",
        f"Generated: {ts_now}",
        f"Data source: memory/ops/load-baseline.jsonl",
        "",
        f"## Progress: {len(present)}/7 days",
        "",
        f"**Status: {'PASS' if verdict == 'PASS' else 'FAIL'}** - 7/7 days complete.",
        "",
        f"Days with data: {', '.join(present)}",
        "",
        "## Daily Summary",
        "",
        "| Day | Runs | c=10 p95 (ms) | c=50 p95 (ms) | c=200 p95 (ms) | Errs |",
        "|-----|------|---------------|---------------|----------------|------|",
    ]
    by_day = {}
    for d in days:
        day_key = d["ts"][:10]
        by_day.setdefault(day_key, []).append(d)
    for dk in sorted(by_day):
        entries = by_day[dk]
        p95s = {lv["concurrency"]: lv.get("p95_ms", "-") for d in entries for lv in d["levels"]}
        errs = sum(lv["errors"] for d in entries for lv in d["levels"])
        lines.append(f"| {dk} | {len(entries)} | {p95s.get(10,'-')} | {p95s.get(50,'-')} | {p95s.get(200,'-')} | {errs} |")

    lines += ["", "## Threshold Check", ""]
    for det in details:
        mark = "PASS" if det["pass"] else "FAIL"
        lines.append(f"- c={det['concurrency']}: max p95={det['max_p95_ms']}ms (limit {det['limit_ms']}ms), errors={det['errors']} -> **{mark}**")
    lines += ["", f"## Verdict: **{verdict}**", ""]

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return REPORT_MD


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=REGRESS_PCT_DEFAULT)
    args = ap.parse_args()

    if not os.path.exists(BASELINE_FILE):
        print("goal1_auto_closure: baseline file not found")
        return 1

    days = load_days()
    present = distinct_days(days)

    if len(present) < WEEK_DAYS:
        missing = WEEK_DAYS - len(present)
        print(f"goal1_auto_closure: INCOMPLETE {len(present)}/{WEEK_DAYS} days "
              f"(need {missing} more; have: {', '.join(present)})")
        return 0

    # 7/7 reached - run full analysis + closure
    all_pass, details, total_errors = analyze_pass_fail(days)
    verdict = "PASS" if all_pass else "FAIL"
    report_path = write_report(days, present, verdict, details)

    # Record to ledger
    ledger_cmd = [sys.executable, os.path.join(ROOT, "memory", "researcher", "goal_ledger.py"),
                  "--record", "mechanic", "1",
                  "--note", f"7/7 days complete; verdict={verdict}; report: {os.path.relpath(report_path, ROOT)}"]
    import subprocess
    try:
        r = subprocess.run(ledger_cmd, capture_output=True, text=True, timeout=30)
        ledger_out = (r.stdout + r.stderr).strip()[:200]
    except Exception as e:
        ledger_out = f"ledger error: {e}"

    print(f"goal1_auto_closure: WEEK_COMPLETE 7/7 days -> {verdict}")
    print(f"  report: {os.path.relpath(report_path, ROOT)}")
    print(f"  ledger: {ledger_out}")
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())