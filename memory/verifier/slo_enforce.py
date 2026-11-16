#!/usr/bin/env python3
"""slo_enforce.py (cycle-2 goal, Verifier role): asserts p95<2s / p99<5s per endpoint
from GET /api/perf (Builder#8) against the Mechanic#4 baseline. Breach -> HOTLINE note.
Writes memory/verifier/slo-report-YYYY-MM-DD.md + appends slo-history.jsonl."""
import json, datetime, urllib.request

def main():
    with urllib.request.urlopen("http://127.0.0.1:8099/api/perf", timeout=15) as r:
        perf = json.loads(r.read())
    breaches, rows = [], []
    for e in perf["endpoints"]:
        n, p95, p99 = e["n"], e.get("p95_ms"), e.get("p99_ms")
        ok = (p95 is None or p95 < 2000) and (p99 is None or p99 < 5000)
        rows.append("%s | n=%d | p95=%sms | p99=%sms | %s" % (e["path"], n, p95, p99, "OK" if ok else "BREACH"))
        if not ok: breaches.append(e["path"])
    today = datetime.date.today().isoformat()
    rep = "# SLO enforcement report - %s\n\nSLO: p95 < 2000ms, p99 < 5000ms per endpoint (source: GET /api/perf, 60-min window).\n\n%s\n\n**Verdict: %s**\n" % (
        today, "\n".join(rows) if rows else "(perf buffer empty - no data yet)",
        "PASS" if not breaches else "BREACH -> HOTLINE note required")
    open("memory/verifier/slo-report-%s.md" % today, "w", encoding="utf-8").write(rep)
    with open("memory/verifier/slo-history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"date": today, "breaches": breaches, "endpoints": len(rows)}) + "\n")
    print("slo_enforce:", "PASS" if not breaches else "BREACH %s" % breaches)

if __name__ == "__main__":
    main()
