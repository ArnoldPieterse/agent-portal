#!/usr/bin/env python3
"""Idle Pass Daily Digest (Scribe goal 3, cycle 15).

At end of day, summarizes idle passes from autoloop.jsonl:
total idle passes, tasks by agent, productive rate, top-3 waste sources.
Output: memory/ops/idle-digest-{date}.md
"""
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
LOG = BASE / "memory" / "ops" / "autoloop.jsonl"
OUT_DIR = BASE / "memory" / "ops"


def load_passes(log_path=None):
    lp = Path(log_path) if log_path else LOG
    out = []
    if not lp.exists():
        return out
    for line in lp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def idle_passes(passes, date_str=None):
    ds = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sel = []
    for r in passes:
        ts = r.get("ts", "")
        if not ts.startswith(ds):
            continue
        if (r.get("task_type") or "").upper() == "IDLE":
            sel.append(r)
    return sel


def build_digest(passes, date_str):
    idle = idle_passes(passes, date_str)
    total = len(idle)
    prod = sum(1 for r in idle if r.get("productive"))
    rate = (prod / total * 100) if total else 0.0
    by_agent = Counter(r.get("agent", "?") for r in idle)
    waste = Counter((r.get("task_text") or "unknown")[:60]
                    for r in idle if not r.get("productive"))
    top3 = waste.most_common(3)
    L = ["# Idle Pass Digest - %s" % date_str, ""]
    L.append("Total idle passes: **%d** (productive: %d, rate %.0f%%)" % (total, prod, rate))
    L.append("")
    L.append("## Tasks by agent")
    L.append("")
    for ag, n in by_agent.most_common():
        L.append("- %s: %d" % (ag, n))
    L.append("")
    L.append("## Top 3 waste sources (non-productive)")
    L.append("")
    if top3:
        for txt, n in top3:
            L.append("- %s x%d" % (txt, n))
    else:
        L.append("- none - all idle passes were productive")
    L.append("")
    return "\n".join(L), {"total": total, "prod": prod, "rate": rate,
                           "by_agent": dict(by_agent), "top3": top3}


def main():
    date_str = None
    if "--date" in sys.argv:
        i = sys.argv.index("--date")
        if i + 1 < len(sys.argv):
            date_str = sys.argv[i + 1]
    ds = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report, stats = build_digest(load_passes(), ds)
    out = OUT_DIR / ("idle-digest-%s.md" % ds)
    out.write_text(report, encoding="utf-8")
    print("Idle digest written to: %s (total=%d)" % (out.name, stats["total"]))


def selftest():
    d = "2099-01-05"
    recs = []
    for i in range(20):
        ag = "a%d" % (i % 4)
        prod = (i % 5 != 0)
        task = "waste-%d" % (i % 3) if not prod else "ok-task"
        recs.append({"ts": d + "T%02d:00:00+00:00" % i, "agent": ag,
                     "task_type": "IDLE", "task_text": task,
                     "productive": prod, "duration_ms": 100})
    rep, st = build_digest(recs, d)
    ok = (st["total"] == 20 and st["prod"] == 16 and abs(st["rate"] - 80.0) < 0.01)
    ok &= (st["by_agent"].get("a0") == 5)
    ok &= ("Total idle passes: **20**" in rep)
    print("Result: %s" % ("PASS" if ok else "FAIL"))
    return ok

if __name__ == "__main__":
    import sys as _s
    if "--selftest" in _s.argv:
        sys.exit(0 if selftest() else 1)
    main()
