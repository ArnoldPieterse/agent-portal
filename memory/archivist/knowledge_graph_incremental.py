#!/usr/bin/env python3
"""archivist/knowledge_graph_incremental.py (cycle-3 goal #1 step, by Scribe 2026-11-18).

Incremental knowledge-graph update: compares current file hashes against the last
manifest, re-processes ONLY changed/new/deleted files for edge extraction, detects
new orphan nodes (no incoming edges), and alerts when orphans appear.

Usage:
  python memory/archivist/knowledge_graph_incremental.py [--quiet]

Exit codes: 0 = clean (no new orphans), 1 = new orphans detected (alert emitted).
Writes updated manifest back to knowledge_graph_manifest.json + appends delta to
knowledge_graph_delta.jsonl.
"""
import hashlib, json, os, re, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "knowledge_graph_manifest.json")
DELTA_LOG = os.path.join(HERE, "knowledge_graph_delta.jsonl")

# Same edge patterns as knowledge_graph.py
PTR = re.compile(r"->\s*([A-Za-z0-9_./\\-]+\.(?:md|py|json|html|css|js))")
MDL = re.compile(r"\[([^\]]*)\]\(([^)]+\.(?:md|py|json|html))\)")
SUP = re.compile(r"(?i)\b(supersedes?|replaced by|superseded by)\s+[:\-]?\s*([A-Za-z0-9_./\\-]+)")

def norm(x): return x.replace("\\", "/").lstrip("./")

def sha1_file(path):
    h = hashlib.sha1()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except Exception:
        return None
    return h.hexdigest()[:16]

def extract_edges(rel, text):
    """Extract outgoing edges from one file's text. Returns list of (target, kind)."""
    edges = []
    for m in PTR.finditer(text):
        t = norm(m.group(1))
        if t != rel:
            edges.append((t, "pointer"))
    for m in MDL.finditer(text):
        t = norm(m.group(2))
        if t != rel:
            edges.append((t, "link"))
    return edges

def main():
    quiet = "--quiet" in sys.argv
    now = datetime.datetime.now().isoformat()

    # Load previous manifest
    prev_hashes = {}
    prev_edges = []  # list of {from, to, kind}
    if os.path.exists(MANIFEST):
        try:
            with open(MANIFEST, encoding="utf-8") as f:
                prev = json.load(f)
            prev_hashes = prev.get("file_hashes", {})
            prev_edges = prev.get("edges", [])
        except Exception:
            pass

    # Walk current tree
    cur_hashes = {}
    for r, d, fs in os.walk(MEM):
        d[:] = [x for x in d if not x.startswith(".")]
        for f in fs:
            p = os.path.join(r, f)
            rel = norm(os.path.relpath(p, ROOT))
            h = sha1_file(p)
            if h:
                cur_hashes[rel] = h

    # Diff
    added = set(cur_hashes) - set(prev_hashes)
    removed = set(prev_hashes) - set(cur_hashes)
    changed = {k for k in set(cur_hashes) & set(prev_hashes) if cur_hashes[k] != prev_hashes[k]}
    unchanged = set(cur_hashes) - added - changed

    # Re-extract edges only for changed/new files; keep old edges for unchanged
    new_edges = []
    # Keep edges where BOTH endpoints are unchanged (or source unchanged and target still exists)
    for e in prev_edges:
        src, dst = e["from"], e["to"]
        if src in unchanged and dst in cur_hashes:
            new_edges.append(e)

    # Extract edges for changed + added files
    for rel in sorted(added | changed):
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for target, kind in extract_edges(rel, text):
            if target in cur_hashes:
                new_edges.append({"from": rel, "to": target, "kind": kind})

    # Orphan detection: nodes with zero incoming edges
    incoming = set(e["to"] for e in new_edges)
    orphans = sorted(set(cur_hashes) - incoming)
    prev_incoming = set(e["to"] for e in prev_edges)
    prev_orphans = sorted(set(prev_hashes) - prev_incoming) if prev_hashes else []
    new_orphans = sorted(set(orphans) - set(prev_orphans))

    # Write updated manifest
    manifest = {
        "generated": now,
        "node_count": len(cur_hashes),
        "edge_count": len(new_edges),
        "file_hashes": cur_hashes,
        "edges": new_edges,
        "orphans": orphans,
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    # Append delta log
    delta = {
        "ts": now,
        "added": sorted(added),
        "removed": sorted(removed),
        "changed": sorted(changed),
        "new_orphans": new_orphans,
        "total_orphans": len(orphans),
    }
    with open(DELTA_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(delta) + "\n")

    # Report
    if not quiet:
        print(f"incremental_graph: {len(cur_hashes)} nodes, {len(new_edges)} edges")
        print(f"  delta: +{len(added)} new, -{len(removed)} removed, ~{len(changed)} changed")
        print(f"  orphans: {len(orphans)} total, {len(new_orphans)} NEW")
        if new_orphans:
            for o in new_orphans[:10]:
                print(f"    NEW ORPHAN: {o}")

    # Exit 1 if new orphans (for alert hook)
    sys.exit(1 if new_orphans else 0)

if __name__ == "__main__":
    main()