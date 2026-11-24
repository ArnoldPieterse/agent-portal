#!/usr/bin/env python3
"""Decision-log compaction (archivist cycle-15 goal 7).

Compresses decision-log.jsonl entries older than 7 days into weekly summary
files memory/archivist/decision-log-week-{ISO-year-Www}.md. Original JSONL
entries are preserved but marked "compacted": true. Idempotent: re-running
never re-summarizes an already-compacted entry and never rewrites a summary
file that already contains the entry's id.

Usage: python memory/archivist/compact_decision_log.py [path-to-jsonl]
"""
import json, os, sys, time
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOG = os.path.join(HERE, "..", "orchestrator", "decision-log.jsonl")
CUTOFF_S = 7 * 86400


def _week_key(ts):
    """ISO year-week label for a unix timestamp, e.g. 2026-W47."""
    t = time.gmtime(ts)
    import datetime as _dt
    d = _dt.date(t.tm_year, t.tm_mon, t.tm_mday)
    y, w, _ = d.isocalendar()
    return "%d-W%02d" % (y, w)


def compact(log_path):
    log_path = os.path.abspath(log_path)
    if not os.path.exists(log_path):
        print("no decision log at", log_path)
        return 0
    entries = []
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                entries.append({"_raw": line})
    now = time.time()
    weeks = OrderedDict()
    changed = 0
    for e in entries:
        ts = e.get("ts") or e.get("timestamp") or 0
        try:
            ts = float(ts)
        except Exception:
            ts = 0.0
        if e.get("compacted") or ts <= 0 or (now - ts) < CUTOFF_S:
            continue
        weeks.setdefault(_week_key(ts), []).append(e)
        e["compacted"] = True
        changed += 1
    # write summaries (append-only per entry id)
    for wk, items in weeks.items():
        out = os.path.join(HERE, "decision-log-week-%s.md" % wk)
        have = set()
        if os.path.exists(out):
            with open(out, encoding="utf-8") as f:
                for l in f:
                    if l.startswith("- id="):
                        have.add(l.split("id=", 1)[1].split()[0])
        fresh = [e for e in items if str(e.get("id", "")) not in have]
        if not fresh and os.path.exists(out):
            continue
        with open(out, "a" if os.path.exists(out) else "w", encoding="utf-8") as f:
            if not os.path.exists(out) or os.path.getsize(out) == 0:
                f.write("# Decision log week %s (compacted from decision-log.jsonl)\n\n" % wk)
            for e in fresh:
                ts = float(e.get("ts") or e.get("timestamp") or 0)
                when = time.strftime("%Y-%m-%d", time.gmtime(ts)) if ts else "?"
                actor = e.get("agent") or e.get("actor") or "?"
                what = e.get("decision") or e.get("text") or e.get("_raw") or "(no text)"
                f.write("- id=%s %s %s: %s\n" % (e.get("id", "-"), when, actor, str(what).replace("\n", " ")[:300]))
    if changed:
        with open(log_path, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
    print("compacted %d entries into %d week file(s)" % (changed, len(weeks)))
    return changed


if __name__ == "__main__":
    compact(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG)
