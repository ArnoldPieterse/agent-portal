#!/usr/bin/env python3
"""archivist/ingest.py (cycle-2 goal 10; A#9 relevance scoring 2026-11-18).
Takes a research output (markdown file or inline text) and writes it into memory/<lane>/
with a provenance header + registers the leaf in that lane's INDEX.md.
A#9: each item is scored against the lane INDEX + memory/INDEX.md corpus; score < 0.7
-> flagged to memory/archivist/ingest-review-queue.md for human review (not auto-indexed).
Usage:
  ingest.py <lane> <source-file-or-text> [confidence] [ttl_days]
  ingest.py --resolve <accept|reject> [item-keyword]   # process the review queue
All decisions are logged to memory/archivist/ingest-decisions.jsonl."""
import os, re, sys, json, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
THRESH = 0.7

def _words(s):
    return {w for w in re.findall(r"[a-z0-9]{4,}", s.lower())}

def score_relevance(body, lane):
    """0..1: how well the body's vocabulary fits this lane (lane INDEX) and the fleet
    corpus (memory/INDEX.md). Scaled linear: lane fit x1.6 + root fit x0.9."""
    b = _words(body) or {"x"}
    li = os.path.join(MEM, lane, "INDEX.md")
    ri = os.path.join(MEM, "INDEX.md")
    L = _words(open(li, encoding="utf-8", errors="replace").read()) if os.path.isfile(li) else set()
    R = _words(open(ri, encoding="utf-8", errors="replace").read()) if os.path.isfile(ri) else set()
    s1 = len(b & L) / len(b); s2 = len(b & R) / len(b)
    return round(min(1.0, 1.6 * s1 + 0.9 * s2), 3)

def _log(decision, lane, score, source):
    p = os.path.join(MEM, "archivist", "ingest-decisions.jsonl")
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                             "decision": decision, "lane": lane, "score": score, "source": source}) + "\n")

def _ingest_body(lane, body, source):
    lane_dir = os.path.join(MEM, lane)
    os.makedirs(lane_dir, exist_ok=True)
    today = datetime.date.today().isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", body[:40].lower()).strip("-")[:32] or "note"
    name = "ingested-%s-%s.md" % (today, slug)
    out = os.path.join(lane_dir, name)
    header = ("# Ingested: %s\n\n- source: %s\n- ingested: %s by archivist/ingest.py (human-accepted)\n"
              "- confidence: medium | ttl_days: 60\n\n---\n\n%s\n") % (slug, source, today, body.strip())
    open(out, "w", encoding="utf-8").write(header)
    rel = "memory/%s/%s" % (lane, name)
    idx = os.path.join(lane_dir, "INDEX.md")
    line = "- -> %s   ingested %s (confidence=medium ttl=60d, human-accepted)\n" % (rel, today)
    if not os.path.isfile(idx):
        open(idx, "w", encoding="utf-8").write("# %s INDEX\nLast updated: %s.\n\n## Entries\n%s" % (lane, today, line))
    elif rel not in open(idx, encoding="utf-8").read():
        open(idx, "a", encoding="utf-8").write(line)

def _resolve(decision, what=None):
    q = os.path.join(MEM, "archivist", "ingest-review-queue.md")
    if not os.path.isfile(q):
        print("no review queue"); return
    t = open(q, encoding="utf-8").read()
    blocks = t.split("\n## QUEUED ")
    out = [blocks[0]]
    for blk in blocks[1:]:
        head, _, rest = blk.partition("\n")
        if "RESOLVED" in head or (what and what.lower() not in (head + rest).lower()):
            out.append("## QUEUED " + blk); continue
        status = "accepted-by-human" if decision == "accept" else "rejected-by-human"
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        out.append("## QUEUED " + blk.replace(head, head + "\n- RESOLVED: %s (%s)" % (status, stamp)))
        if decision == "accept":
            m = re.search(r"lane=(\S+)", blk)
            if m: _ingest_body(m.group(1), rest, "human-accepted (was score-flagged)")
        _log(decision + "-resolve", what or head[:40], 0.0, status)
        print("resolve: %s -> %s" % (decision, (what or head[:48]))); return
    open(q, "w", encoding="utf-8").write("\n".join(out))
    print("queue item not found:", what or "(latest)")

def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--resolve":
        if len(sys.argv) < 3 or sys.argv[2] not in ("accept", "reject"):
            print("usage: ingest.py --resolve <accept|reject> [item-keyword]"); raise SystemExit(2)
        _resolve(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None); raise SystemExit(0)
    if len(sys.argv) < 3:
        print("usage: ingest.py <lane> <source-file-or-text> [confidence] [ttl_days]"); raise SystemExit(2)
    lane, src = sys.argv[1], sys.argv[2]
    conf = sys.argv[3] if len(sys.argv) > 3 else "medium"
    ttl = sys.argv[4] if len(sys.argv) > 4 else "60"
    if os.path.isfile(src):
        body = open(src, encoding="utf-8", errors="replace").read(); source = src
    else:
        body = src; source = "inline (studio session)"
    score = score_relevance(body, lane)
    if score < THRESH:
        q = os.path.join(MEM, "archivist", "ingest-review-queue.md")
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if not os.path.isfile(q):
            open(q, "w", encoding="utf-8").write("# Ingest Review Queue (A#9)\nItems below the relevance threshold (0.7) await a human decision.\nResolve with: python memory/archivist/ingest.py --resolve <accept|reject> [keyword]\n")
        open(q, "a", encoding="utf-8").write("\n## QUEUED %s lane=%s score=%.3f source=%s\n%s\n---\n" % (ts, lane, score, source, body.strip()[:400]))
        _log("flagged-for-review", lane, score, source)
        print("ingest: FLAGGED for human review (score %.3f < %.1f) -> memory/archivist/ingest-review-queue.md" % (score, THRESH))
        raise SystemExit(3)
    lane_dir = os.path.join(MEM, lane)
    os.makedirs(lane_dir, exist_ok=True)
    today = datetime.date.today().isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", body[:40].lower()).strip("-")[:32] or "note"
    name = "ingested-%s-%s.md" % (today, slug)
    out = os.path.join(lane_dir, name)
    header = ("# Ingested: %s\n\n- source: %s\n- ingested: %s by archivist/ingest.py\n"
              "- confidence: %s | ttl_days: %s | relevance_score: %.3f\n\n---\n\n%s\n") % (slug, source, today, conf, ttl, score, body.strip())
    open(out, "w", encoding="utf-8").write(header)
    rel = "memory/%s/%s" % (lane, name)
    idx = os.path.join(lane_dir, "INDEX.md")
    line = "- -> %s   ingested %s (confidence=%s ttl=%sd score=%.3f)\n" % (rel, today, conf, ttl, score)
    if not os.path.isfile(idx):
        open(idx, "w", encoding="utf-8").write("# %s INDEX\nLast updated: %s.\n\n## Entries\n%s" % (lane, today, line))
    else:
        t = open(idx, encoding="utf-8").read()
        if rel not in t:
            open(idx, "a", encoding="utf-8").write(line)
    _log("auto-indexed", lane, score, source)
    print("ingest: wrote %s (%d chars, confidence=%s ttl=%sd score=%.3f), indexed" % (rel, len(body), conf, ttl, score))

if __name__ == "__main__":
    main()
