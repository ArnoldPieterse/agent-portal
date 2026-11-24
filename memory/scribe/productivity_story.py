#!/usr/bin/env python3
"""Productivity Story - weekly fleet narrative (Scribe goal 4, cycle 15).

5-8 sentences on productivity evolution over the last 7 days of autoloop.jsonl:
direction, which agents improved/declined, what interventions helped.
Every number is computed from the log file - nothing is invented.
Output: memory/synthesis/productivity-week-{ISO}.md
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
LOG = BASE / "memory" / "ops" / "autoloop.jsonl"
OUT_DIR = BASE / "memory" / "synthesis"


def load_passes(days=7):
    if not LOG.exists():
        return []
    cutoff = (datetime.now(timezone.utc).timestamp() - days * 86400)
    out = []
    for line in LOG.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
            if r.get("ts") and datetime.fromisoformat(r["ts"]).timestamp() >= cutoff:
                out.append(r)
        except Exception:
            pass
    return out


def agent_stats(recs):
    st = {}
    by = defaultdict(list)
    for r in recs:
        by[r.get("agent", "?")].append(bool(r.get("productive")))
    for ag, prods in by.items():
        n = len(prods)
        st[ag] = {"n": n, "rate": 100.0 * sum(prods) / n if n else 0.0}
    return st


def build_story(recs):
    S = []
    if not recs:
        return ("No auto-loop passes were recorded in the last 7 days - "
                "the pass logger went live during this cycle, so no trend can be computed yet. "
                "The fleet's first productivity story will appear once a week of pass data has accumulated."), None
    n = len(recs)
    prod = sum(1 for r in recs if r.get("productive"))
    rate = 100.0 * prod / n
    S.append("Over the last 7 days the fleet completed %d auto-loop passes, of which %d (%.1f%%) were productive." % (n, prod, rate))
    st = agent_stats(recs)
    ranked = sorted(st.items(), key=lambda kv: (-kv[1]["rate"], -kv[1]["n"]))
    if ranked:
        top = ranked[0]
        S.append("Top performer: %s at %.1f%% productive across %d passes." % (top[0], top[1]["rate"], top[1]["n"]))

    if len(ranked) > 1:
        low = ranked[-1]
        S.append("Needs attention: %s at %.1f%% productive across %d passes." % (low[0], low[1]["rate"], low[1]["n"]))
    half = n // 2
    r1 = sum(1 for r in recs[:half] if r.get("productive")) / max(half, 1) * 100
    r2 = sum(1 for r in recs[half:] if r.get("productive")) / max(n - half, 1) * 100
    if r2 > r1 + 5:
        S.append("Direction: improving - the second half of the window ran at %.1f%% versus %.1f%% in the first half." % (r2, r1))
    elif r1 > r2 + 5:
        S.append("Direction: declining - the second half fell to %.1f%% from %.1f%%." % (r2, r1))
    else:
        S.append("Direction: steady - both halves of the window stayed within 5 points (%.1f%% vs %.1f%%)." % (r1, r2))

    waste = Counter(r.get("task_text", "?") for r in recs if not r.get("productive"))
    if waste:
        w = waste.most_common(1)[0]
        S.append("Most frequent non-productive task type: '%s' (%d times) - the prime intervention target." % (w[0], w[1]))
    S = S[:8]
    return "\n\n".join(S), {"total": n, "prod": prod, "rate": rate}


def main():
    recs = load_passes(7)
    story, stats = build_story(recs)
    iso = datetime.now(timezone.utc).strftime("%G-W%V")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / ("productivity-week-%s.md" % iso)
    out.write_text("# Productivity Story - Week %s\n\n%s\n" % (iso, story), encoding="utf-8")
    print("Productivity story written to: %s (%d passes)" % (out, len(recs)))


def selftest():
    import tempfile
    global LOG
    real = LOG
    td = Path(tempfile.mkdtemp())
    LOG = td / "autoloop.jsonl"
    recs = []
    for i in range(14):
        prod = (i >= 7)  # first half 0%, second half 100% -> improving
        recs.append({"ts": datetime.now(timezone.utc).isoformat(), "agent": "x",
                     "task_type": "IDLE", "task_text": "w" if not prod else "ok",
                     "productive": prod, "duration_ms": 1})
    LOG.write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    story, st = build_story(load_passes())
    ok = (st["total"] == 14 and "improving" in story.lower() and len(story.split(". ")) <= 8)
    LOG = real
    print("Result: %s" % ("PASS" if ok else "FAIL"))
    return ok


if __name__ == "__main__":
    import sys as _s
    if "--selftest" in _s.argv:
        sys.exit(0 if selftest() else 1)
    main()
