#!/usr/bin/env python
"""
Goal #6 (Researcher, cycle-6) - Overnight-unload correlation: per-hour histogram.

Reads the unified load/latency feed (memory/ops/load-baseline.jsonl) and any
per-host result JSONs, buckets UNLOAD / MISS / LOAD events by HOUR-OF-DAY,
and reports whether the unload/miss mass concentrates in overnight hours vs
daylight. This is the quantitative companion to the qualitative CLOSED leaf
memory/llm/overnight-unload.md (H1 JIT-TTL vs H2 host-power-state).

Event classification (per row):
  - kind=='load' rows: verdict ALL_UP -> 'load_success'; any failed/skipped model
    or non-ALL_UP verdict -> 'load_miss'.
  - latency-probe rows (kind absent/'latency'): carry NO unload/miss signal
    (they are throughput benchmarks); counted separately so they never pollute
    the histogram, but their timestamps still bound the observation window.

Honest low-N handling: if fewer than MIN_N event rows exist, the tool prints an
explicit LOW-N banner and a verdict of INSUFFICIENT-DATA rather than a fabricated
trend. This is the correct outcome today (the feed holds 1 synthetic load row +
4 latency rows; zero real unload/miss events).

Run:  python memory/researcher/overnight_unload_histogram.py [--feed PATH] [--json]
"""
import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FEED = os.path.join(HERE, "..", "ops", "load-baseline.jsonl")
MIN_N = 5            # minimum real event rows for a non-trivial trend claim
NIGHT_HOURS = set(range(0, 9)) | {23}   # 23:00-08:59 treated as 'overnight'


def _parse_ts(raw):
    """Return (datetime, ok). Tolerates both feed ts formats."""
    import datetime
    if not raw:
        return None, False
    s = str(raw).replace("T", " ")[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.datetime.strptime(s, fmt), True
        except ValueError:
            continue
    return None, False


def _classify(d):
    """Map one feed row to an event label (or None if it carries no unload/miss signal)."""
    kind = d.get("kind", "latency")
    if isinstance(d.get("levels"), list) or kind == "latency":
        return "latency_probe"          # throughput benchmark, not an unload/miss event
    if kind == "load":
        verdict = str(d.get("verdict", "")).upper()
        failed = int(d.get("models_failed", 0) or 0)
        skipped = int(d.get("models_skipped", 0) or 0)
        if verdict == "ALL_UP" and failed == 0:
            return "load_success"
        return "load_miss"
    return None


def collect_events(feed_path, extra_jsons=None):
    events = []   # list of dicts: {ts, hour, host, event}
    latency_ts = []
    for path in [feed_path] + (extra_jsons or []):
        if not path or not os.path.exists(path):
            continue
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except (ValueError, json.JSONDecodeError):
                    continue
                dt, ok = _parse_ts(d.get("ts"))
                if not ok:
                    continue
                label = _classify(d)
                rec = {"ts": str(dt), "hour": dt.hour, "host": d.get("host", "?"), "event": label}
                if label == "latency_probe":
                    latency_ts.append(str(dt))
                elif label is not None:
                    events.append(rec)
    return events, sorted(latency_ts)


def build_histogram(events):
    by_hour = Counter(e["hour"] for e in events)
    night = sum(c for h, c in by_hour.items() if h in NIGHT_HOURS)
    day = sum(c for h, c in by_hour.items() if h not in NIGHT_HOURS)
    return by_hour, night, day


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", default=DEFAULT_FEED)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--result-jsons-glob", default=os.path.join(HERE, "..", "..", "*load*result*.json"))
    args = ap.parse_args(argv)

    extra = sorted(glob.glob(args.result_jsons_glob))
    events, latency_ts = collect_events(os.path.abspath(args.feed), extra)
    by_hour, night, day = build_histogram(events)
    real_n = len(events)
    sufficient = real_n >= MIN_N

    if sufficient and (night + day) > 0:
        frac = night / (night + day)
        if frac >= 0.7:
            verdict = "OVERNIGHT-CONCENTRATED (supports H1/H2; see leaf for discriminator)"
        elif frac <= 0.3:
            verdict = "DAYLIGHT-CONCENTRATED (argues AGAINST overnight-unload framing)"
        else:
            verdict = "UNIFORM (no clear overnight signal in current data)"
    elif real_n > 0:
        verdict = f"LOW-N: {real_n} event row(s) < MIN_N={MIN_N}; no trend claim made"
    else:
        verdict = "INSUFFICIENT-DATA: zero unload/miss event rows in feed yet"

    out = {
        "feed": os.path.abspath(args.feed),
        "extra_jsons": extra,
        "real_event_rows": real_n,
        "latency_probe_rows": len(latency_ts),
        "observation_window": {"first": latency_ts[0] if latency_ts else None,
                               "last": latency_ts[-1] if latency_ts else None},
        "events_by_hour": {str(h): by_hour.get(h, 0) for h in range(24)},
        "night_count": night, "day_count": day,
        "sufficient_data": sufficient,
        "verdict": verdict,
    }
    if args.json:
        print(json.dumps(out, indent=2))
        return 0
    print("=== Overnight-unload per-hour histogram (goal #6) ===")
    print(f"feed               : {out['feed']}")
    print(f"extra result JSONs : {len(extra)}")
    print(f"real event rows    : {real_n}   (latency-probe rows: {len(latency_ts)})")
    w = out["observation_window"]
    print(f"observation window : {w['first']}  ->  {w['last']}")
    print("--- events by hour-of-day (00..23) ---")
    row = ""
    for h in range(24):
        c = by_hour.get(h, 0)
        bar = "#" * c
        row += f"{h:02d}:{bar}"
        if (h + 1) % 8 == 0:
            print(row); row = ""
    if row:
        print(row)
    print(f"--- night(23-08):{night}  day(09-22):{day} ---")
    print(f"VERDICT: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
