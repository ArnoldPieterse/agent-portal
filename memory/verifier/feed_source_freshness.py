#!/usr/bin/env python3
"""feed_source_freshness.py (2026-11-24, Verifier): feed-vs-source data-staleness gate.

Gap it fills: gap_alarm.py only watches git HEAD age (commit silence). It cannot
catch the case where cockpit-feed.json IS being rewritten (fresh mtime) but its
embedded data `ts` lags the newest line in fleet-metrics.jsonl. This checker
measures that *data* lag and fails closed when it exceeds a threshold.

Exit codes:
  0 = FRESH   (lag <= THRESHOLD_MIN)
  1 = STALE   (lag >  THRESHOLD_MIN) -> writes memory/ops/feed-staleness.json flag + log line
  2 = ERROR   (feed or source missing / unparseable ts)

CWD-robust: all paths anchored via __file__ (repo root is two levels up from this file).
Self-test: --self-test builds temp FRESH/STALE/MISSING fixtures and asserts exit codes.
"""
import json, os, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FEED = os.path.join(REPO_ROOT, "memory", "ops", "cockpit-feed.json")
SOURCE = os.path.join(REPO_ROOT, "memory", "ops", "fleet-metrics.jsonl")
FLAG = os.path.join(REPO_ROOT, "memory", "ops", "feed-staleness.json")
LOG = os.path.join(REPO_ROOT, "memory", "ops", "feed-staleness.log")
THRESHOLD_MIN = 45


def parse_ts(s):
    if not s:
        return None
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d


def feed_ts(path=FEED):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    for k in ("ts", "timestamp", "generated_at"):
        if isinstance(d, dict) and d.get(k):
            return parse_ts(d[k])
    return None


def source_ts(path=SOURCE):
    last = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            t = parse_ts(rec.get("timestamp") or rec.get("ts"))
            if t and (last is None or t > last):
                last = t
    return last


def check(feed=FEED, source=SOURCE, threshold_min=THRESHOLD_MIN):
    """Return (exit_code, lag_minutes_or_None, detail)."""
    try:
        ft = feed_ts(feed)
    except Exception as e:
        return 2, None, "feed missing/unreadable: %s" % e
    try:
        st = source_ts(source)
    except Exception as e:
        return 2, None, "source missing/unreadable: %s" % e
    if ft is None or st is None:
        return 2, None, "unparseable ts (feed=%s source=%s)" % (ft, st)
    lag_min = (st - ft).total_seconds() / 60.0
    if lag_min > threshold_min:
        return 1, round(lag_min, 1), "STALE: feed lags newest source by %.1f min (> %d)" % (lag_min, threshold_min)
    return 0, round(lag_min, 1), "FRESH: feed lags newest source by %.1f min (<= %d)" % (lag_min, threshold_min)


def emit_flag(code, lag):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if code == 1:
        try:
            os.makedirs(os.path.dirname(FLAG), exist_ok=True)
            with open(FLAG, "w", encoding="utf-8") as f:
                json.dump({"active": True, "lag_min": lag, "threshold_min": THRESHOLD_MIN, "ts": now}, f)
            with open(LOG, "a", encoding="utf-8") as f:
                f.write("%s STALE: feed lags source by %s min (>%d)\n" % (now, lag, THRESHOLD_MIN))
        except Exception:
            pass
    elif code == 0 and os.path.exists(FLAG):
        try:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write("%s clear: feed fresh (lag %s min)\n" % (now, lag))
            os.remove(FLAG)
        except Exception:
            pass


def main(argv):
    if "--self-test" in argv:
        return self_test()
    code, lag, detail = check()
    emit_flag(code, lag)
    print("feed_source_freshness: %s [lag=%s min]" % (detail, lag))
    return code


def _write_feed(path, ts):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"ts": ts, "data": {}}, f)


def _write_source(path, ts):
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": ts, "host": "T"}) + "\n")


def self_test():
    import tempfile
    base = dt.datetime(2026, 11, 23, 20, 0, 0, tzinfo=dt.timezone.utc)
    iso = lambda m: (base + dt.timedelta(minutes=m)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    tmp = tempfile.mkdtemp(prefix="fsf_")
    feed = os.path.join(tmp, "feed.json")
    src = os.path.join(tmp, "src.jsonl")
    results = []

    def run(name, expect):
        code, lag, detail = check(feed=feed, source=src)
        ok = (code == expect)
        results.append((name, ok, code, expect, detail))

    # T1 FRESH: feed 10 min old vs source now -> lag ~ -? make feed newer-ish
    _write_feed(feed, iso(50)); _write_source(src, iso(60))   # source 10min after feed
    run("T1_fresh", 0)
    # T2 STALE: feed far behind source
    _write_feed(feed, iso(0)); _write_source(src, iso(90))     # lag 90 > 45
    run("T2_stale", 1)
    # T3 boundary at threshold (45 exactly -> not >, so FRESH)
    _write_feed(feed, iso(0)); _write_source(src, iso(45))
    run("T3_boundary_fresh", 0)
    # T4 just over threshold
    _write_feed(feed, iso(0)); _write_source(src, iso(46))
    run("T4_just_over_stale", 1)
    # T5 missing source -> ERROR
    os.remove(src) if os.path.exists(src) else None
    _write_feed(feed, iso(10))
    run("T5_missing_source", 2)
    # T6 unparseable ts -> ERROR
    with open(src, "w", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": "not-a-date"}) + "\n")
    run("T6_bad_ts", 2)

    passed = sum(1 for r in results if r[1])
    for name, ok, code, expect, detail in results:
        print("  [%s] %s got=%d want=%d (%s)" % ("PASS" if ok else "FAIL", name, code, expect, detail))
    print("feed_source_freshness --self-test: %d/%d PASS" % (passed, len(results)))
    return 0 if passed == len(results) else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
