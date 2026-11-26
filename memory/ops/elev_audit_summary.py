"""elev_audit_summary.py - Weekly anomaly summary for elevated command audit trail.

Reads memory/ops/elev-audit.jsonl, computes:
  - Top-3 most frequent commands (by prefix)
  - Any command with >5 consecutive failures
  - Total call count, success rate, avg duration

Output: prints to stdout + appends to memory/ops/elev-audit-summary.jsonl

Usage: python memory/ops/elev_audit_summary.py [--days N]  (default 7)
"""
import json, sys, time
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

AUDIT_LOG = Path("memory/ops/elev-audit.jsonl")
SUMMARY_LOG = Path("memory/ops/elev-audit-summary.jsonl")

def load_records(days=7):
    if not AUDIT_LOG.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    records = []
    with AUDIT_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ts = datetime.fromisoformat(rec["ts"])
                if ts >= cutoff:
                    records.append(rec)
            except (json.JSONDecodeError, KeyError):
                continue
    return records

def cmd_prefix(cmd, n=3):
    """First N tokens as a normalized command key."""
    parts = cmd.split()
    return " ".join(parts[:n]) if len(parts) >= n else cmd

def find_consecutive_failures(records, threshold=5):
    """Find runs of >threshold consecutive failures for same command prefix."""
    by_cmd = defaultdict(list)
    for rec in records:
        by_cmd[cmd_prefix(rec["cmd"])].append(rec)
    
    alerts = []
    for cmd_key, recs in by_cmd.items():
        run = 0
        for rec in recs:
            if rec["exit_code"] != 0:
                run += 1
                if run == threshold + 1:  # first time we exceed threshold
                    alerts.append({
                        "command": cmd_key,
                        "consecutive_failures": run,
                        "since": recs[-run]["ts"],
                    })
            else:
                run = 0
    return alerts

def main():
    days = 7
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        days = int(sys.argv[idx + 1])

    records = load_records(days)
    
    if not records:
        print(f"[elev-audit-summary] No records in last {days} days.")
        return

    # Stats
    total = len(records)
    successes = sum(1 for r in records if r["exit_code"] == 0)
    success_rate = round(successes / total * 100, 1) if total else 0
    avg_ms = round(sum(r["duration_ms"] for r in records) / total, 1) if total else 0

    # Top commands
    cmd_counter = Counter(cmd_prefix(r["cmd"]) for r in records)
    top3 = cmd_counter.most_common(3)

    # Consecutive failure alerts
    fail_alerts = find_consecutive_failures(records, threshold=5)

    summary = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "window_days": days,
        "total_calls": total,
        "success_rate_pct": success_rate,
        "avg_duration_ms": avg_ms,
        "top3_commands": [{"cmd": c, "count": n} for c, n in top3],
        "consecutive_failure_alerts": fail_alerts,
    }

    # Write summary
    SUMMARY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")

    # Print
    print(f"[elev-audit-summary] Window: {days}d | Calls: {total} | Success: {success_rate}% | Avg: {avg_ms}ms")
    print(f"  Top commands:")
    for c, n in top3:
        print(f"    {n:4d}x  {c}")
    if fail_alerts:
        print(f"  ALERTS ({len(fail_alerts)}):")
        for a in fail_alerts:
            print(f"    >{a['consecutive_failures']} consecutive failures: {a['command']}")
    else:
        print("  No consecutive failure alerts.")

if __name__ == "__main__":
    main()
