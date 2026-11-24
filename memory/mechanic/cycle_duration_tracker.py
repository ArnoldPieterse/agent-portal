#!/usr/bin/env python3
"""cycle_duration_tracker.py - Rolling 3-cycle mean+stddev; flag if current > mean+2*sigma.

Reads memory/ops/cycle-durations.jsonl, computes stats, writes summary to stdout.
Usage: python memory/mechanic/cycle_duration_tracker.py [--selftest]
"""
import json, os, sys, statistics
from datetime import datetime, timezone

DURATIONS_PATH = os.path.join("memory", "ops", "cycle-durations.jsonl")


def load_durations():
    if not os.path.exists(DURATIONS_PATH):
        return []
    entries = []
    with open(DURATIONS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def compute_stats(entries):
    """Rolling 3-cycle mean+stddev; flag current if > mean+2*sigma."""
    durs = [e["duration_hours"] for e in entries]
    if len(durs) < 4:
        return {"n": len(durs), "mean": None, "stddev": None, "threshold": None,
                "current": durs[-1] if durs else None, "flagged": False}
    # Rolling window: the 3 cycles BEFORE current (not including it)
    prior3 = durs[-4:-1]
    mean = statistics.mean(prior3)
    stdev = statistics.stdev(prior3) if len(prior3) >= 2 else 0.0
    current = durs[-1]
    threshold = mean + 2 * stdev
    return {
        "n": len(durs),
        "mean": round(mean, 2),
        "stddev": round(stdev, 2),
        "threshold": round(threshold, 2),
        "current": current,
        "flagged": current > threshold,
    }


def selftest():
    """Verify outlier flagging works: inject a spike and confirm it's flagged."""
    ok = True
    def check(name, cond):
        nonlocal ok
        print(("PASS" if cond else "FAIL"), name)
        ok = ok and bool(cond)

    # Normal entries (4) -> no flag
    normal = [
        {"cycle": 1, "duration_hours": 24.0},
        {"cycle": 2, "duration_hours": 26.0},
        {"cycle": 3, "duration_hours": 25.0},
        {"cycle": 4, "duration_hours": 27.0},
    ]
    s = compute_stats(normal)
    check("normal: no flag", s["flagged"] is False)

    # Spike entry -> flagged (prior3=[26,25,27] mean=26,std~1, threshold~28; current=100 > 28)
    spike = normal + [{"cycle": 5, "duration_hours": 100.0}]
    s = compute_stats(spike)
    check("spike: flagged (>mean+2*sigma)", s["flagged"] is True)

    # Fewer than 4 entries -> safe, no crash
    s = compute_stats(normal[:3])
    check("short: safe (no crash)", s["flagged"] is False and s["mean"] is None)

    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    entries = load_durations()
    stats = compute_stats(entries)
    out = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **stats,
    }
    print(json.dumps(out, indent=2))
    if stats["flagged"]:
        print(f"ALERT: cycle duration {stats['current']}h exceeds threshold {stats['threshold']}h")
    sys.exit(0)


if __name__ == "__main__":
    main()
