"""WF2: Weekly Performance Report Generator

Input : metrics.jsonl  (one JSON object per line: {date, metric, value})
Output: report.md      (formatted weekly report with trend arrows)
Logic : Group by metric, compute week-over-week delta, flag anomalies (>2 std dev).

Usage:
    python wf2_weekly_report.py --selftest
    python wf2_weekly_report.py --input metrics.jsonl --output report.md
"""
import json, sys, argparse, statistics
from datetime import date, timedelta
from pathlib import Path

def load_metrics(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def group_by_metric(records: list[dict]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for r in records:
        out.setdefault(r["metric"], []).append(r["value"])
    return out

def compute_report(records: list[dict], week_end: date) -> str:
    grouped = group_by_metric(records)
    lines = [f"# Weekly Report — week ending {week_end.isoformat()}", ""]
    for metric, values in sorted(grouped.items()):
        if len(values) < 2:
            continue
        recent, prior = values[-7:], values[-14:-7]
        if not prior:
            prior = values[:len(recent)]
        avg_r = sum(recent) / len(recent)
        avg_p = sum(prior) / len(prior) if prior else 0
        delta = ((avg_r - avg_p) / avg_p * 100) if avg_p else 0
        arrow = "\u25b2" if delta > 0 else ("\u25bc" if delta < 0 else "\u2014")
        all_vals = values
        mean = statistics.mean(all_vals)
        stdev = statistics.stdev(all_vals) if len(all_vals) > 1 else 0
        anomaly = "**ANOMALY**" if stdev and abs(avg_r - mean) > 2 * stdev else ""
        lines.append(f"- **{metric}**: {avg_r:.1f} ({arrow} {delta:+.1f}% WoW) {anomaly}")
    lines.append("")
    return "\n".join(lines)

def selftest():
    # Simulate 2 weeks of data for 2 metrics
    records = []
    base = date(2026, 11, 9)
    for i in range(14):
        d = (base + timedelta(days=i)).isoformat()
        records.append({"date": d, "metric": "revenue", "value": 100 + i * 5})
        records.append({"date": d, "metric": "tickets_closed", "value": 20 + (i % 3)})
    report = compute_report(records, date(2026, 11, 22))
    assert "revenue" in report
    assert "tickets_closed" in report
    assert "\u25b2" in report  # revenue trending up
    assert "# Weekly Report" in report
    print("WF2 selftest PASS: 4/4 assertions")
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if args.selftest:
        sys.exit(0 if selftest() else 1)
    records = load_metrics(args.input)
    report = compute_report(records, date.today())
    args.output.write_text(report, encoding="utf-8")
    print(f"WF2: report generated ({len(records)} data points) -> {args.output}")

if __name__ == "__main__":
    main()