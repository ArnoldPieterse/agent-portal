#!/usr/bin/env python3
"""load_probe.py (2026-11-16, Mechanic cycle-2 goal 3): concurrent GETs at 10/50/200
against :8099 (/api/goals + /), p50/p95/p99 per level -> memory/ops/load-baseline.jsonl.

OUTAGE GUARD (2026-11-17, Orchestrator): a fully-down portal must NOT poison the baseline
with all-error rows (they lack p50/p95 keys and break load_trend.py history reads). If a level
is 100% errors it is marked skipped='all_errors' and excluded from the baseline row; if EVERY
level is down, nothing is appended to load-baseline.jsonl and one line goes to
load-outage.jsonl (reason=all_endpoints_down) instead. Pinned via PIN_FILES in memory_mirror.py
so the mirror's LWW pull-back from a stale remote can no longer revert this guard (observed 3x)."""
import json, time, datetime, os, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "http://127.0.0.1:8099"   # override in tests; schtask runs from any CWD (paths are __file__-relative)

def one(path):
    t0 = time.time()
    try:
        with urllib.request.urlopen(BASE + path, timeout=15) as r:
            r.read(4096); code = r.status
    except Exception as e:
        return (time.time() - t0) * 1000, str(e)[:40]
    return (time.time() - t0) * 1000, code

def level(n):
    paths = ["/api/goals", "/"]
    with ThreadPoolExecutor(max_workers=n) as ex:
        res = list(ex.map(lambda p: one(p), [paths[i % 2] for i in range(n)]))
    ms = sorted(r[0] for r in res)
    errs = sum(1 for r in res if isinstance(r[1], str) and r[1] != "200")
    if errs == n:   # OUTAGE GUARD: level fully down -> exclude from baseline, never fake a p50/p95
        return {"concurrency": n, "n": n, "skipped": "all_errors", "errors": errs}
    def pct(q):
        k = (len(ms) - 1) * q / 100; f = int(k); c = min(f + 1, len(ms) - 1)
        return round(ms[f] + (ms[c] - ms[f]) * (k - f), 1)
    return {"concurrency": n, "n": n, "p50_ms": pct(50), "p95_ms": pct(95),
            "p99_ms": pct(99), "errors": errs}

def main():
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    levels = [level(n) for n in (10, 50, 200)]
    good = [lv for lv in levels if "skipped" not in lv]
    here = os.path.dirname(os.path.abspath(__file__))
    if not good:   # total outage -> do NOT write a baseline row; log the outage instead
        with open(os.path.join(here, "load-outage.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.datetime.now().astimezone().isoformat(),
                                "seat": "white", "portal_url": BASE,
                                "reason": "all_endpoints_down"}) + "\n")
        print("load_probe: OUTAGE (all levels down) -> load-outage.jsonl, baseline untouched")
        return
    out = {"ts": ts, "levels": good}
    with open(os.path.join(here, "load-baseline.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(out) + "\n")
    print("load_probe:", json.dumps(good[1] if len(good) > 1 else good[0]))

if __name__ == "__main__":
    main()
