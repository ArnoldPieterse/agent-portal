#!/usr/bin/env python3
"""archivist/knowledge_graph.py (cycle-2 goal 1).
Walks every memory/ leaf, extracts cross-references (-> path pointers, markdown links,
'see also'/'supersedes' markers) and emits a JSON dependency graph + rendered text map.
Exit 0 always; --json writes knowledge_graph.json next to this file."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
PTR = re.compile(r"->\s*([A-Za-z0-9_./\\-]+\.(?:md|py|json|html|css|js))")
MDL = re.compile(r"\[([^\]]*)\]\(([^)]+\.(?:md|py|json|html))\)")
SUP = re.compile(r"(?i)\b(supersedes?|replaced by|superseded by)\s+[:\-]?\s*([A-Za-z0-9_./\\-]+)")

def norm(x): return x.replace("\\", "/").lstrip("./")

def main():
    edges, sup = [], []
    files = {}
    texts = {}
    # PASS 1: collect every file (full membership set) before extracting any
    # edges. The old single-pass version checked `t in files` against a set that
    # was still being built during the walk, so an edge only registered if its
    # target happened to be walked BEFORE its source -- making orphan counts
    # depend on filesystem listdir order (e.g. basenames sorting after INDEX.md).
    for r, d, fs in os.walk(MEM):
        d[:] = [x for x in d if not x.startswith(".")]
        for f in fs:
            p = os.path.join(r, f)
            rel = norm(os.path.relpath(p, ROOT))
            files[rel] = os.path.getmtime(p)
    # PASS 2: now that `files` is complete, extract edges from each file's text.
    for r, d, fs in os.walk(MEM):
        d[:] = [x for x in d if not x.startswith(".")]
        for f in fs:
            p = os.path.join(r, f)
            rel = norm(os.path.relpath(p, ROOT))
            try: txt = open(p, encoding="utf-8", errors="replace").read()
            except Exception: continue
            for m in PTR.finditer(txt):
                t = norm(m.group(1))
                if t in files and t != rel: edges.append({"from": rel, "to": t, "kind": "pointer"})
            for m in MDL.finditer(txt):
                t = norm(m.group(2))
                if t in files and t != rel: edges.append({"from": rel, "to": t, "kind": "link"})
            for m in SUP.finditer(txt):
                sup.append({"from": rel, "target": norm(m.group(2)), "marker": m.group(1)})
    graph = {"root": os.path.basename(ROOT), "node_count": len(files),
             "edge_count": len(edges), "supersession_edges": len(sup),
             "edges": edges, "supersessions": sup}
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_graph.json")
    if "--json" in sys.argv or True:
        json.dump(graph, open(out, "w", encoding="utf-8"), indent=1)
    # rendered text map (top hubs by out-degree)
    deg = {}
    for e in edges: deg[e["from"]] = deg.get(e["from"], 0) + 1
    print("knowledge_graph: %d nodes, %d edges, %d supersession markers -> %s"
          % (len(files), len(edges), len(sup), os.path.relpath(out, ROOT)))
    for k, v in sorted(deg.items(), key=lambda kv: -kv[1])[:8]:
        print("  hub(%d): %s" % (v, k))

if __name__ == "__main__":
    main()
