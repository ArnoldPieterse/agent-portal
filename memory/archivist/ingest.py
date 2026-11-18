#!/usr/bin/env python3
"""archivist/ingest.py (cycle-2 goal 10).
Takes a research output (markdown file or inline text) and writes it into memory/<lane>/
with a provenance header (source, date, confidence, TTL) + registers the leaf in that
lane's INDEX.md. Usage: ingest.py <lane> <source-file-or-text> [confidence] [ttl_days]."""
import os, re, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
THRESH = 0.7
QUEUE = os.path.join(MEM, "archivist", "ingest-review-queue.md")
DECLOG = os.path.join(MEM, "archivist", "ingest-decisions.jsonl")

def _words(s):
    return {w for w in re.findall(r"[a-z0-9]{4,}", s.lower())}

def score_relevance(body, lane):
    b = _words(body) or {"x"}
    li = os.path.join(MEM, lane, "INDEX.md")
    ri = os.path.join(MEM, "INDEX.md")
    L = _words(open(li, encoding="utf-8", errors="replace").read()) if os.path.isfile(li) else set()
    R = _words(open(ri, encoding="utf-8", errors="replace").read()) if os.path.isfile(ri) else set()
    s1 = len(b & L) / len(b)
    s2 = len(b & (R | {lane})) / len(b)
    return round(min(1.0, 1.6 * s1 + 0.9 * s2), 3)  # scaled: lane fit x1.6 + root fit x0.9

def _log(decision, lane, score, source):
    import json
    open(DECLOG, "a", encoding="utf-8").write(json.dumps({
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "decision": decision, "lane": lane, "score": score, "source": source}) + "\n")

def _resolve(what):
    if not os.path.isfile(QUEUE):
        print("no review queue"); return
    blocks = open(QUEUE, encoding="utf-8").read().split("\n## QUEUED ")[1:]
    hit = None
    for blk in blocks:
        head, _, rest = blk.partition("\n")
        if what.lower() in (head + rest).lower():
            hit = blk; break
    if not hit:
        print("queue item not found: %s" % what); return
    lane = re.search(r"lane=(\S+)", hit).group(1)
    body = hit.split("---\n")[-1].strip()
    status = "accepted" if what == "accept" else "rejected-by-human"
    if what == "accept":
        today = datetime.date.today().isoformat()
        slug = re.sub(r"[^a-z0-9]+", "-", body[:40].lower()).strip("-")[:32] or "note"
        name = "ingested-%s-%s.md" % (today, slug)
        out = os.path.join(MEM, lane, name)
        open(out, "w", encoding="utf-8").write(
            "# Ingested: %s\n\n- source: human-resolved from review queue\n- ingested: %s by archivist/ingest.py --resolve\n\n---\n\n%s\n" % (slug, today, body))
        rel = "memory/%s/%s" % (lane, name)
        open(os.path.join(MEM, lane, "INDEX.md"), "a", encoding="utf-8").write("- -> %s   human-accepted %s\n" % (rel, today))
    _log(status, lane, None, "review-queue")
    t2 = open(QUEUE, encoding="utf-8").read().replace("## QUEUED " + hit.split("\n")[0], "## RESOLVED(%s) " % what + hit.split("\n")[0])
    open(QUEUE, "w", encoding="utf-8").write(t2)
    print("resolved: %s lane=%s" % (what, lane))

def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--resolve":
        _resolve(sys.argv[2]); return
    if len(sys.argv) < 3:
        print("usage: ingest.py <lane> <source-file-or-text> [confidence] [ttl_days]"); raise SystemExit(2)
    lane, src = sys.argv[1], sys.argv[2]
    conf = sys.argv[3] if len(sys.argv) > 3 else "medium"
    ttl = sys.argv[4] if len(sys.argv) > 4 else "60"
    if os.path.isfile(src):
        body = open(src, encoding="utf-8", errors="replace").read()
        source = src
    else:
        body = src
        source = "inline (studio session)"
    score = score_relevance(body, lane)
    if score < THRESH:
        today = datetime.date.today().isoformat()
        os.makedirs(os.path.dirname(QUEUE), exist_ok=True)
        open(QUEUE, "a", encoding="utf-8").write(
            "\n## QUEUED %s lane=%s score=%.3f source=%s\n%s\n---\n" % (today, lane, score, source, body[:400]))
        _log("flagged-for-review", lane, score, source)
        print("ingest: FLAGGED for human review (score %.3f < %.1f) -> %s" % (score, THRESH, QUEUE))
        raise SystemExit(3)
    lane_dir = os.path.join(MEM, lane)
    os.makedirs(lane_dir, exist_ok=True)
    today = datetime.date.today().isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", body[:40].lower()).strip("-")[:32] or "note"
    name = "ingested-%s-%s.md" % (today, slug)
    out = os.path.join(lane_dir, name)
    header = ("# Ingested: %s\n\n"
              "- source: %s\n- ingested: %s by archivist/ingest.py\n"
              "- confidence: %s | ttl_days: %s\n\n---\n\n%s\n") % (slug, source, today, conf, ttl, body.strip())
    open(out, "w", encoding="utf-8").write(header)
    rel = "memory/%s/%s" % (lane, name)
    idx = os.path.join(lane_dir, "INDEX.md")
    line = "- -> %s   ingested %s (confidence=%s ttl=%sd)\n" % (rel, today, conf, ttl)
    if not os.path.isfile(idx):
        open(idx, "w", encoding="utf-8").write("# %s INDEX\nLast updated: %s.\n\n## Entries\n%s" % (lane, today, line))
    else:
        t = open(idx, encoding="utf-8").read()
        if rel not in t:
            open(idx, "a", encoding="utf-8").write(line)
    print("ingest: wrote %s (%d chars, confidence=%s ttl=%sd), indexed" % (rel, len(body), conf, ttl))
    _log("auto-indexed", lane, score, source)

if __name__ == "__main__":
    main()def _ingest_body(lane, body, source):
    lane_dir = os.path.join(MEM, lane)
    os.makedirs(lane_dir, exist_ok=True)
    today = datetime.date.today().isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", body[:40].lower()).strip("-")[:32] or "note"
    name = "ingested-%s-%s.md" % (today, slug)
    out = os.path.join(lane_dir, name)
    header = ("# Ingested: %s\n\n- source: %s\n- ingested: %s by archivist/ingest.py (human-accepted)\n- confidence: medium | ttl_days: 60\n\n---\n\n%s\n") % (slug, source, today, body.strip())
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
        out.append("## QUEUED " + blk.replace(head, head + "\n- RESOLVED: %s (%s)" % (status, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))))
        if decision == "accept":
            m = re.search(r"lane=(\S+)", blk)
            if m: _ingest_body(m.group(1), rest, "human-accepted (was score-flagged)")
        log_decision(decision + "-resolve", what or head[:40], 0.0, status)
        print("resolve: %s -> %s" % (decision, (what or head[:48]))); return
    out.append("")
    open(q, "w", encoding="utf-8").write("\n".join(out))
    if what is None and decision not in ("accept", "reject"): print("queue item not found")

def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--resolve":
        _resolve(sys.argv[2]); return
    if len(sys.argv) < 3:
        print("usage: ingest.py <lane> <source-file-or-text> [confidence] [ttl_days]"); raise SystemExit(2)
    lane, src = sys.argv[1], sys.argv[2]
    conf = sys.argv[3] if len(sys.argv) > 3 else "medium"
    ttl = sys.argv[4] if len(sys.argv) > 4 else "60"
    if os.path.isfile(src):
        body = open(src, encoding="utf-8", errors="replace").read()
        source = src
    else:
        body = src
        source = "inline (studio session)"
    score = score_relevance(body, lane)
    if score < THRESH:
        today = datetime.date.today().isoformat()
        os.makedirs(os.path.dirname(QUEUE), exist_ok=True)
        open(QUEUE, "a", encoding="utf-8").write(
            "\n## QUEUED %s lane=%s score=%.3f source=%s\n%s\n---\n" % (today, lane, score, source, body[:400]))
        _log("flagged-for-review", lane, score, source)
        print("ingest: FLAGGED for human review (score %.3f < %.1f) -> %s" % (score, THRESH, QUEUE))
        raise SystemExit(3)
    lane_dir = os.path.join(MEM, lane)
    os.makedirs(lane_dir, exist_ok=True)
    today = datetime.date.today().isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", body[:40].lower()).strip("-")[:32] or "note"
    name = "ingested-%s-%s.md" % (today, slug)
    out = os.path.join(lane_dir, name)
    header = ("# Ingested: %s\n\n"
              "- source: %s\n- ingested: %s by archivist/ingest.py\n"
              "- confidence: %s | ttl_days: %s\n\n---\n\n%s\n") % (slug, source, today, conf, ttl, body.strip())
    open(out, "w", encoding="utf-8").write(header)
    rel = "memory/%s/%s" % (lane, name)
    idx = os.path.join(lane_dir, "INDEX.md")
    line = "- -> %s   ingested %s (confidence=%s ttl=%sd)\n" % (rel, today, conf, ttl)
    if not os.path.isfile(idx):
        open(idx, "w", encoding="utf-8").write("# %s INDEX\nLast updated: %s.\n\n## Entries\n%s" % (lane, today, line))
    else:
        t = open(idx, encoding="utf-8").read()
        if rel not in t:
            open(idx, "a", encoding="utf-8").write(line)
    print("ingest: wrote %s (%d chars, confidence=%s ttl=%sd), indexed" % (rel, len(body), conf, ttl))
    _log("auto-indexed", lane, score, source)

if __name__ == "__main__":
    main()
