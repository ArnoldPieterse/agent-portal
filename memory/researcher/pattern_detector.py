#!/usr/bin/env python
"""
Pattern Recurrence Detector (Researcher goal #7, cycle 15 - Fleet Autonomy Convergence).

Scans memory/ops/decision-log.jsonl for root-cause keywords/phrases that recur in the
last 7 days. A "recurrence" is measured as the number of log entries in the window whose
text exhibits a given root-cause pattern (entry-frequency, not raw token count). For each
pattern it reports: count, first_seen, last_seen, affected_agents.

Output: memory/ops/recurring-patterns.json  (ranked by frequency, descending).
Threshold: flag patterns with count > 3 (i.e. >=4) in the window.

Two detection layers:
  1. LEXICON   - a curated set of known root-cause phrases (deterministic, primary).
  2. AUTO      - repeated content-word trigrams appearing in >threshold distinct entries,
                 deduped against already-flagged lexicon patterns (catches novel recurrences).

Verification acceptance criteria (goal #7):
  - On synthetic data with 4 known patterns (one at threshold 3, the rest above), the
    detector finds all above-threshold patterns correctly and excludes the boundary case;
    ranking is by frequency descending.
Both are exercised by `python memory/researcher/pattern_detector.py --self-test`.
"""
from __future__ import annotations
import json
import re
import os
import sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DECISION_LOG = os.path.join(ROOT, "memory", "ops", "decision-log.jsonl")
OUTPUT = os.path.join(ROOT, "memory", "ops", "recurring-patterns.json")

SEATS = {"researcher", "builder", "verifier", "designer", "archivist",
         "scribe", "mechanic", "orchestrator"}

# Curated root-cause lexicon: lowercase phrase -> canonical pattern label.
LEXICON = {
    "mirror revert": "Mirror revert (index.html pin clobber)",
    "clobber loop": "Pin file clobber loop",
    "pin clobber": "Pin file clobber loop",
    "stale verify": "Stale verification claim",
    "stale claim": "Stale verification claim",
    "false positive": "False-positive verification",
    "dangling pointer": "Dangling/orphan pointer",
    "orphan pointer": "Dangling/orphan pointer",
    "out of memory": "OOM / host resource exhaustion",
    "oom kill": "OOM / host resource exhaustion",
    "model not loaded": "Model not loaded on home host",
    "not loaded": "Model not loaded on home host",
    "seat unreachable": "Seat unreachable (reroute)",
    "unreachable": "Seat unreachable (reroute)",
    "budget exhausted": "Pass budget exhausted",
    "stale >30min": "Stale seat (>30min) reroute",
    "stale >30 min": "Stale seat (>30min) reroute",
}

_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "by",
    "that", "this", "was", "were", "is", "are", "be", "been", "as", "at", "its",
    "it", "from", "pass", "passes", "sync", "mode", "agent", "agents", "work",
}


def _parse_ts(value):
    if value is None:
        return None
    s = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _read_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _entry_text(rec):
    """Concatenate the textual fields of a decision-log entry (lowercased)."""
    parts = []
    for k, v in rec.items():
        if k in ("timestamp", "ts"):
            continue
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            for x in v:
                if isinstance(x, str):
                    parts.append(x)
                elif isinstance(x, dict):
                    parts.extend(str(y) for y in x.values() if isinstance(y, str))
        elif isinstance(v, dict):
            parts.extend(str(y) for y in v.values() if isinstance(y, str))
    return " ".join(parts).lower()


def _entry_agents(rec):
    agents = set()
    a = rec.get("agent")
    if isinstance(a, str) and a.lower() in SEATS:
        agents.add(a.lower())
    for field in ("unreachable", "reroutes", "seats", "agents"):
        v = rec.get(field)
        items = v if isinstance(v, list) else [v]
        for it in items:
            if isinstance(it, str) and it.lower() in SEATS:
                agents.add(it.lower())
            elif isinstance(it, dict):
                for kk in ("from", "to", "agent"):
                    if isinstance(it.get(kk), str) and it[kk].lower() in SEATS:
                        agents.add(it[kk].lower())
    return agents


def _trigrams(text):
    words = [w for w in re.findall(r"[a-z0-9]+", text) if w not in _STOP and len(w) > 2]
    grams = set()
    for i in range(len(words) - 2):
        g = " ".join(words[i:i + 3])
        grams.add(g)
    return grams


def detect(entries, now=None, window_days=7, threshold=3, use_auto=True):
    """
    Core detector. `entries` is a list of decision-log dicts (each with a timestamp-like
    field). Returns a list of pattern dicts sorted by count desc:
      {pattern, kind(lexicon|auto), count, first_seen, last_seen, affected_agents}
    Flags patterns with count > threshold (strictly greater).
    """
    if now is None:
        now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)

    # index: pattern_label -> {count, first, last, agents}
    stats = {}

    def bump(label, kind, dt, agents):
        s = stats.setdefault(label, {"pattern": label, "kind": kind,
                                     "count": 0, "first": None, "last": None,
                                     "agents": set()})
        s["count"] += 1
        if dt is not None:
            if s["first"] is None or dt < s["first"]:
                s["first"] = dt
            if s["last"] is None or dt > s["last"]:
                s["last"] = dt
        s["agents"].update(agents)

    # trigram accumulator (only distinct entries count per gram)
    tri_entries = {}

    for rec in entries:
        dt = _parse_ts(rec.get("timestamp") or rec.get("ts"))
        if dt is not None and dt < cutoff:
            continue  # outside window
        text = _entry_text(rec)
        agents = _entry_agents(rec)
        matched_labels = set()
        for phrase, label in LEXICON.items():
            if phrase in text:
                bump(label, "lexicon", dt, agents)
                matched_labels.add(label)
        if use_auto:
            grams = _trigrams(text)
            for g in grams:
                tri_entries.setdefault(g, {"count": 0, "first": None, "last": None,
                                            "agents": set()})
                t = tri_entries[g]
                t["count"] += 1
                if dt is not None:
                    if t["first"] is None or dt < t["first"]:
                        t["first"] = dt
                    if t["last"] is None or dt > t["last"]:
                        t["last"] = dt
                t["agents"].update(agents)

    # fold in auto trigrams that exceed threshold and aren't already covered by a lexicon hit
    for g, t in tri_entries.items():
        if t["count"] <= threshold:
            continue
        # skip if this trigram is contained in an already-flagged lexicon pattern's phrase set
        covered = any(g in phrase or phrase in g for phrase in LEXICON)
        if covered:
            continue
        label = f"auto:{g}"
        bump(label, "auto", t["first"], t["agents"])

    out = []
    for s in stats.values():
        if s["count"] <= threshold:      # flag only count > threshold (strictly greater)
            continue
        out.append({
            "pattern": s["pattern"],
            "kind": s["kind"],
            "count": s["count"],
            "first_seen": s["first"].isoformat() if s["first"] else None,
            "last_seen": s["last"].isoformat() if s["last"] else None,
            "affected_agents": sorted(s["agents"]),
        })
    # rank by frequency desc; tie-break: last_seen desc (None-safe), then name asc
    out.sort(key=lambda r: (-r["count"],
                            r["last_seen"] or "",
                            r["pattern"]))
    return out


def run(window_days=7, threshold=3):
    entries = _read_jsonl(DECISION_LOG)
    now = datetime.now(timezone.utc)
    patterns = detect(entries, now=now, window_days=window_days, threshold=threshold)
    cutoff = now - timedelta(days=window_days)
    in_window = 0
    for e in entries:
        dt = _parse_ts(e.get("timestamp") or e.get("ts"))
        if dt is not None and dt >= cutoff:
            in_window += 1
    payload = {
        "generated": now.isoformat(),
        "source": os.path.relpath(DECISION_LOG, ROOT).replace("\\", "/"),
        "window_days": window_days,
        "threshold": f">{threshold}",
        "entries_in_window": in_window,
        "pattern_count": len(patterns),
        "patterns": patterns,
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return payload


def self_test():
    now = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)

    def mk(ts_h, agent, text):
        return {"timestamp": now.replace(hour=ts_h % 24, minute=0).isoformat(),
                "agent": agent, "detail": text}

    entries = []
    # A: 'mirror revert' x7 -> flag (rank by count)
    for h in range(7):
        entries.append(mk(h, "designer", f"index.html pin mirror revert detected pass {h}"))
    # B: 'oom kill' x6 -> flag
    for h in range(7, 13):
        if h - 7 < 6:
            entries.append(mk(h + 1, "mechanic", f"host white oom kill of model {h}"))
    # C: 'stale verify' x5 -> flag
    for h in range(13, 18):
        if h - 13 < 5:
            entries.append(mk(h + 1, "verifier", f"stale verify claim on goal {h}"))
    # D: 'unreachable' x4 -> flag (exactly above threshold)
    for h in range(18, 22):
        if h - 18 < 4:
            entries.append(mk(h + 1, "orchestrator", f"seat {h} unreachable reroute"))
    # E: 'budget exhausted' x3 -> BOUNDARY, must be EXCLUDED (not >3)
    for h in range(22, 25):
        if h - 22 < 3:
            entries.append(mk(h + 1, "scribe", f"pass budget exhausted cycle {h}"))

    res = detect(entries, now=now, window_days=7, threshold=3, use_auto=False)
    labels = [r["pattern"] for r in res]
    counts = [r["count"] for r in res]

    ok = True
    expected_above = {
        "Mirror revert (index.html pin clobber)": 7,
        "OOM / host resource exhaustion": 6,
        "Stale verification claim": 5,
        "Seat unreachable (reroute)": 4,
    }
    boundary = "Pass budget exhausted"
    # all above-threshold present with correct counts
    for lab, cnt in expected_above.items():
        if lab not in labels:
            print(f"  FAIL: missing expected pattern {lab}")
            ok = False
        else:
            got = counts[labels.index(lab)]
            if got != cnt:
                print(f"  FAIL: {lab} count={got} expected {cnt}")
                ok = False
    # boundary excluded
    if boundary in labels:
        print("  FAIL: boundary pattern (count=3) should be excluded")
        ok = False
    # ranking strictly by frequency descending
    if counts != sorted(counts, reverse=True):
        print(f"  FAIL: not ranked desc: {counts}")
        ok = False
    # every result has required fields
    for r in res:
        for k in ("pattern", "count", "first_seen", "last_seen", "affected_agents"):
            if k not in r:
                print(f"  FAIL: missing field {k} in {r['pattern']}")
                ok = False
    print(f"PATTERNS found={len(res)} counts={counts}")
    for r in res:
        print(f"  [{r['count']:>2}] {r['pattern']}  agents={r['affected_agents']}")
    print("SELF-TEST:", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


def main(argv):
    if "--self-test" in argv:
        return self_test()
    window = 7
    threshold = 3
    for i, a in enumerate(argv):
        if a == "--window" and i + 1 < len(argv):
            window = int(argv[i + 1])
        if a == "--threshold" and i + 1 < len(argv):
            threshold = int(argv[i + 1])
    payload = run(window_days=window, threshold=threshold)
    print(f"Pattern detector: entries_in_window={payload['entries_in_window']} "
          f"patterns(>{threshold})={payload['pattern_count']}")
    for r in payload["patterns"][:10]:
        print(f"  [{r['count']:>2}] {r['pattern']}")
    print(f"output -> {os.path.relpath(OUTPUT, ROOT).replace(chr(92), '/')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
