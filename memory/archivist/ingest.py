#!/usr/bin/env python3
"""archivist/ingest.py (cycle-2 goal 10).
Takes a research output (markdown file or inline text) and writes it into memory/<lane>/
with a provenance header (source, date, confidence, TTL) + registers the leaf in that
lane's INDEX.md. Usage: ingest.py <lane> <source-file-or-text> [confidence] [ttl_days]."""
import os, re, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")

def main():
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

if __name__ == "__main__":
    main()
