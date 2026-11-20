#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_decisions.py - Scribe goal #1 (cycle-7): Decision Auto-Extraction.

Scans chat logs + goal/synthesis files for decision patterns and structures them
into memory/synthesis/decisions.jsonl with {date, decision, context, owner, confidence}.

Usage:
    python memory/scribe/extract_decisions.py --since YYYY-MM-DD [--min-conf 0.6] [--dry-run]

Design notes (false-positive control):
  - Patterns are tiered by strength; each match carries a confidence score.
  - Negative filters drop meta/question lines ("DECISION NEEDED", "no further decisions").
  - Dedup on normalized decision text so the same call repeated across files counts once.
  - Owner is inferred from speaker attribution (chat) or an agent name on the line.
"""
import os, re, sys, json, argparse
from datetime import date

ROOT = "."
OUT = "memory/synthesis/decisions.jsonl"
AGENTS = ["Orchestrator", "Researcher", "Builder", "Verifier", "Designer",
          "Archivist", "Mechanic", "Scribe"]
HUMAN = ["human", "arnold", "user"]

# (compiled, confidence). Order matters: first match wins per line.
PATTERNS = [
    (re.compile(r"\bratified\b", re.I), 0.9),
    (re.compile(r"\bagreed\s*(?:to|:|that)\b", re.I), 0.85),
    (re.compile(r"\bdecision\s*[:=]\s*\S", re.I), 0.85),
    (re.compile(r"\bresolved\s+that\b", re.I), 0.8),
    (re.compile(r"\bwe\s+will\s+(?:adopt|use|go with|implement|move to)\b", re.I), 0.75),
    (re.compile(r"\bdecided\s+to\b", re.I), 0.75),
    (re.compile(r"\badopted\b", re.I), 0.7),
    (re.compile(r"\bthe plan is to\b", re.I), 0.65),
    (re.compile(r"going forward,\s+we\b", re.I), 0.6),
]

NEGATIVE = re.compile(
    r"DECISION NEEDED|no further decision|decision was not|not a decision|"
    r"pending decision|awaiting decision|revisit the decision|"
    r"^Source:|^\s*-\s*->", re.I)


def infer_owner(line):
    low = line.lower()
    for a in AGENTS:
        if a.lower() in low:
            return a
    for h in HUMAN:
        if h in low:
            return "human"
    return "(unattributed)"


def clean(text):
    # strip markdown emphasis + leading list/bullet markers, collapse whitespace
    t = re.sub(r"[*_`>]+", " ", text)
    t = re.sub(r"^[-+•]\s*", "", t.strip())
    return re.sub(r"\s+", " ", t).strip(" :.-")


def norm_key(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())[:80]


def date_from_name(fname):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
    return m.group(1) if m else None


def iter_sources(since):
    """Yield (source_label, date, [(owner_hint, line), ...])."""
    # 1) chat history (speaker field = owner)
    chat = os.path.join(ROOT, "chat_history_group.json")
    if os.path.exists(chat):
        try:
            hist = json.load(open(chat, encoding="utf-8")).get("history", [])
        except Exception:
            hist = []
        for m in hist:
            owner = m.get("speaker", "(unattributed)")
            if owner == "You":
                owner = "human"
            yield ("chat_history_group.json", None, [(owner, ln) for ln in m.get("content", "").split("\n")])
    # 2) goal + synthesis .md files
    for sub in ("memory/goals", "memory/synthesis"):
        d = os.path.join(ROOT, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".md") or f == "INDEX.md":
                continue
            p = os.path.join(d, f)
            fd = date_from_name(f)
            if since and fd and fd < since:
                continue
            try:
                lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
            except Exception:
                continue
            yield (os.path.relpath(p, ROOT), fd, [("", ln) for ln in lines])


def extract(since=None, min_conf=0.6):
    seen = {}
    for source, fdate, lines in iter_sources(since):
        for hint, raw in lines:
            if NEGATIVE.search(raw):
                continue
            line = raw.strip()
            if len(line) < 12 or len(line) > 400:
                continue
            conf = None
            for pat, c in PATTERNS:
                if pat.search(line):
                    conf = c
                    break
            if conf is None or conf < min_conf:
                continue
            decision = clean(line)
            if len(decision) < 15:
                continue
            owner = hint if hint and hint != "" else infer_owner(line)
            key = norm_key(decision)
            # keep highest-confidence / first-seen per normalized text
            if key in seen:
                if conf > seen[key]["confidence"]:
                    seen[key]["confidence"] = conf
                continue
            d = fdate or (source.split("/")[-1][:10] if re.match(r"\d{4}-", source.split("/")[-1]) else "unknown")
            seen[key] = {
                "date": d,
                "decision": decision[:300],
                "context": f"from {source}",
                "owner": owner,
                "confidence": round(conf, 2),
            }
    return list(seen.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None, help="only include files dated >= this YYYY-MM-DD")
    ap.add_argument("--min-conf", type=float, default=0.6)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    entries = extract(args.since, args.min_conf)
    # sort by date then confidence desc
    entries.sort(key=lambda e: (e["date"], -e["confidence"]))

    print(f"Extracted {len(entries)} unique decisions (min-conf {args.min_conf}, since={args.since})")
    dist = {}
    for e in entries:
        bucket = "high(>=0.8)" if e["confidence"] >= 0.8 else "med(0.6-0.8)"
        dist[bucket] = dist.get(bucket, 0) + 1
    print("Confidence distribution:", dist)
    print("Owners:", {o: sum(1 for e in entries if e["owner"] == o) for o in sorted({e['owner'] for e in entries})})

    for e in entries[:8]:
        print(f"  [{e['confidence']}] ({e['date']}, {e['owner']}) {e['decision'][:80]}")

    if not args.dry_run:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        print(f"Wrote {len(entries)} entries -> {os.path.relpath(OUT, ROOT)}")

    # acceptance self-check
    ok = len(entries) >= 10 and all(all(k in e for k in ("date", "decision", "context", "owner", "confidence")) for e in entries)
    print("ACCEPTANCE (>=10 + all fields):", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
