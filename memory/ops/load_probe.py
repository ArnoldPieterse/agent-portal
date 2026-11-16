#!/usr/bin/env python3
"""load_probe.py (2026-11-16, Mechanic cycle-2 goal 3): concurrent GETs at 10/50/200
against :8099 (/api/goals + /), p50/p95/p99 per level -> memory/ops/load-baseline.jsonl."""
import json, time, datetime, urllib.request, statistics
from concurrent.futures import ThreadPoolExecutor

def one(path):
    t0 = time.time()
    try:
        with urllib.request.urlopen("http://127.0.0.1:8099" + path, timeout=15) as r:
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
    def pct(q):
        k = (len(ms) - 1) * q / 100; f = int(k); c = min(f + 1, len(ms) - 1)
        return round(ms[f] + (ms[c] - ms[f]) * (k - f), 1)
    return {"concurrency": n, "n": n, "p50_ms": pct(50), "p95_ms": pct(95),
            "p99_ms": pct(99), "errors": errs}

out = {"ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
       "levels": [level(n) for n in (10, 50, 200)]}
with open("memory/ops/load-baseline.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(out) + "\n")
print("load_probe:", json.dumps({k: v for k, v in out["levels"][1].items()}))

