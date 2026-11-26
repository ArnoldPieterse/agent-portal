#!/usr/bin/env python3
"""
elev_audit_summary.py - Weekly summary for elevated command audit trail.
Reads memory/ops/elev-audit.jsonl and produces:
  - Top-3 most frequent commands
  - Any runs with >5 consecutive failures (exit_code != 0)
  - Total call count, success rate, avg duration

Usage:
  python memory/mechanic/elev_audit_summary.py          (print summary)
  python memory/mechanic/elev_audit_summary.py --json   (JSON output)
  python memory/mechanic/elev_audit_summary.py selftest
"""
import json, sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

AUDIT_LOG = Path("memory/ops/elev-audit.jsonl")
SUMMARY_OUT = Path("memory/ops/elev-audit-summary-latest.json")


def load_entries(since_hours=168):
    """Load audit entries from last N hours (default 7 days)."""
    if not AUDIT_LOG.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    entries = []
    for line in AUDIT_LOG.read_text(encoding='utf-8').strip().split('\n'):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            ts = datetime.fromisoformat(e['ts'].replace('Z', '+00:00'))
            if ts >= cutoff:
                entries.append(e)
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    return entries


def compute_summary(entries):
    """Compute summary stats from audit entries."""
    if not entries:
        return {"total_calls": 0, "success_rate_pct": 100.0, "avg_duration_ms": 0,
                "top3_commands": [], "consecutive_failure_streaks": []}

    total = len(entries)
    successes = sum(1 for e in entries if e.get('exit_code', -1) == 0)
    durations = [e.get('duration_ms', 0) for e in entries]

    # Top-3 most frequent commands
    cmd_counts = Counter(e.get('cmd', 'unknown') for e in entries)
    top3 = [(cmd, cnt) for cmd, cnt in cmd_counts.most_common(3)]

    # Find consecutive failure streaks >5
    streaks = []
    current_streak = 0
    streak_start = None
    for i, e in enumerate(entries):
        if e.get('exit_code', -1) != 0:
            if current_streak == 0:
                streak_start = e.get('ts')
            current_streak += 1
        else:
            if current_streak > 5:
                streaks.append({"length": current_streak, "start_ts": streak_start,
                                "end_ts": entries[i-1].get('ts')})
            current_streak = 0
    # Check trailing streak
    if current_streak > 5:
        streaks.append({"length": current_streak, "start_ts": streak_start,
                        "end_ts": entries[-1].get('ts')})

    return {
        "total_calls": total,
        "success_rate_pct": round((successes / total) * 100, 1),
        "avg_duration_ms": round(sum(durations) / len(durations), 1) if durations else 0,
        "top3_commands": [{"cmd": c, "count": n} for c, n in top3],
        "consecutive_failure_streaks": streaks,
    }


def selftest():
    print("=== elev_audit_summary.py selftest ===")
    passed = 0
    failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  ok   - {name}")
        else:
            failed += 1
            print(f"  FAIL - {name}")

    # Test with real data
    entries = load_entries(since_hours=9999)  # all time
    check("audit log has entries", len(entries) > 0)

    summary = compute_summary(entries)
    check("summary has total_calls", summary["total_calls"] == len(entries))
    check("summary has success_rate_pct", 0 <= summary["success_rate_pct"] <= 100)
    check("top3_commands is list of dicts",
          isinstance(summary["top3_commands"], list) and
          all(isinstance(x, dict) and "cmd" in x for x in summary["top3_commands"]))
    check("top3 has at most 3 entries", len(summary["top3_commands"]) <= 3)

    # Test consecutive failure detection with synthetic data
    synthetic = []
    base_ts = datetime.now(timezone.utc).isoformat()
    for i in range(7):
        synthetic.append({"ts": base_ts, "cmd": f"fail_cmd_{i}", "exit_code": 1, "duration_ms": 100})
    synthetic.append({"ts": base_ts, "cmd": "good_cmd", "exit_code": 0, "duration_ms": 50})

    syn_summary = compute_summary(synthetic)
    check("detects >5 consecutive failures (7 in row)",
          len(syn_summary["consecutive_failure_streaks"]) == 1)
    check("streak length correct", 
          syn_summary["consecutive_failure_streaks"][0]["length"] == 7 if syn_summary["consecutive_failure_streaks"] else False)

    # Test no false positive on short streaks
    short_fail = [{"ts": base_ts, "cmd": f"f{i}", "exit_code": 1, "duration_ms": 50} for i in range(3)]
    short_fail.append({"ts": base_ts, "cmd": "ok", "exit_code": 0, "duration_ms": 50})
    short_summary = compute_summary(short_fail)
    check("no false positive on 3-consecutive failures",
          len(short_summary["consecutive_failure_streaks"]) == 0)

    # Write summary file
    real_summary = compute_summary(load_entries())
    real_summary["generated_at"] = datetime.now(timezone.utc).isoformat()
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.write_text(json.dumps(real_summary, indent=2), encoding='utf-8')
    check("summary file written", SUMMARY_OUT.exists())

    print(f"\n=== Results: {passed} PASS, {failed} FAIL ===")
    return failed == 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        ok = selftest()
        sys.exit(0 if ok else 1)

    entries = load_entries()
    summary = compute_summary(entries)
    summary["generated_at"] = datetime.now(timezone.utc).isoformat()

    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print(json.dumps(summary, indent=2))
    else:
        print(f"Elevated Command Audit Summary ({summary['generated_at'][:19]}Z)")
        print(f"  Total calls (7d): {summary['total_calls']}")
        print(f"  Success rate:     {summary['success_rate_pct']}%")
        print(f"  Avg duration:     {summary['avg_duration_ms']}ms")
        print(f"  Top-3 commands:")
        for item in summary["top3_commands"]:
            print(f"    {item['count']:4d}x  {item['cmd']}")
        if summary["consecutive_failure_streaks"]:
            print(f"  ALERT: {len(summary['consecutive_failure_streaks'])} failure streak(s) >5")
            for s in summary["consecutive_failure_streaks"]:
                print(f"    {s['length']} consecutive failures: {s['start_ts'][:19]} -> {s['end_ts'][:19]}")
        else:
            print("  No failure streaks >5")

    # Also write to file
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2), encoding='utf-8')


if __name__ == "__main__":
    main()
