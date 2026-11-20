#!/usr/bin/env python3
"""archivist/kg_export.py (cycle-7 goal 10).
Export the knowledge graph to JSON-LD; verify round-trip integrity.
Usage:
  python memory/archivist/kg_export.py --format jsonld [--out PATH]
  python memory/archivist/kg_export.py --verify-roundtrip
"""
import json, os, sys, tempfile, shutil
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GRAPH_JSON = os.path.join(HERE, "knowledge_graph.json")

JSONLD_CONTEXT = {
    "@context": {
        "@vocab": "https://schema.org/",
        "kg": "https://fleet-memory.example.org/kg#",
        "node": "kg:Node",
        "edge": "kg:Edge",
        "supersession": "kg:Supersession",
        "path": "kg:path",
        "kind": "kg:kind",
        "marker": "kg:marker",
        "exportedAt": "kg:exportedAt",
        "nodeCount": "kg:nodeCount",
        "edgeCount": "kg:edgeCount"
    }
}

def load_graph():
    """Load graph from knowledge_graph.json; regenerate if missing."""
    if os.path.exists(GRAPH_JSON):
        with open(GRAPH_JSON, encoding="utf-8") as f:
            return json.load(f)
    # Fall back: run the walker
    sys.path.insert(0, HERE)
    import knowledge_graph as kg
    kg.main()
    with open(GRAPH_JSON, encoding="utf-8") as f:
        return json.load(f)

def to_jsonld(graph):
    """Convert internal graph dict to JSON-LD list of @graph entries."""
    now = datetime.now(timezone.utc).isoformat()
    nodes = []
    edges = []
    sups = []

    # Collect all unique file paths as nodes
    node_set = set()
    for e in graph.get("edges", []):
        node_set.add(e["from"])
        node_set.add(e["to"])
    # Also include files that are isolated (in the full file list but no edges)
    # We don't have the full file list here, so nodes = endpoints of edges + supersession targets
    for s in graph.get("supersessions", []):
        node_set.add(s["from"])
        node_set.add(s["target"])

    for path in sorted(node_set):
        nodes.append({
            "@type": "kg:Node",
            "@id": f"kg://{path}",
            "path": path
        })

    for e in graph.get("edges", []):
        edges.append({
            "@type": "kg:Edge",
            "@id": f"kg://edge/{e['from']}->{e['to']}/{e['kind']}",
            "source": {"@id": f"kg://{e['from']}"},
            "target": {"@id": f"kg://{e['to']}"},
            "kind": e["kind"]
        })

    for s in graph.get("supersessions", []):
        sups.append({
            "@type": "kg:Supersession",
            "@id": f"kg://sup/{s['from']}->{s['target']}/{s['marker']}",
            "source": {"@id": f"kg://{s['from']}"},
            "target": {"@id": f"kg://{s['target']}"},
            "marker": s["marker"]
        })

    # Top-level metadata node
    meta = {
        "@type": "kg:Graph",
        "@id": f"kg://graph/{graph.get('root', 'fleet')}",
        "exportedAt": now,
        "nodeCount": graph.get("node_count", len(node_set)),
        "edgeCount": graph.get("edge_count", len(edges))
    }

    return {"@context": JSONLD_CONTEXT["@context"], "@graph": [meta] + nodes + edges + sups}

def export_jsonld(out_path=None):
    graph = load_graph()
    jsonld = to_jsonld(graph)
    if out_path is None:
        out_path = os.path.join(HERE, "kg-export.jsonld")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(jsonld, f, indent=1, ensure_ascii=False)
    n_nodes = sum(1 for x in jsonld["@graph"] if x.get("@type") == "kg:Node")
    n_edges = sum(1 for x in jsonld["@graph"] if x.get("@type") == "kg:Edge")
    n_sups  = sum(1 for x in jsonld["@graph"] if x.get("@type") == "kg:Supersession")
    try:
        disp = os.path.relpath(out_path, ROOT)
    except ValueError:
        disp = out_path
    print(f"kg_export: wrote {disp} ({os.path.getsize(out_path)} bytes)")
    print(f"  nodes={n_nodes} edges={n_edges} supersessions={n_sups}")
    return out_path

def verify_roundtrip():
    """Export to temp dir, re-import, compare metrics. Returns (pass, detail)."""
    # Step 1: export
    tmpdir = tempfile.mkdtemp(prefix="kg_rt_")
    try:
        out_path = os.path.join(tmpdir, "kg-export.jsonld")
        export_jsonld(out_path)

        # Step 2: import (read back the JSON-LD)
        with open(out_path, encoding="utf-8") as f:
            imported = json.load(f)

        # Step 3: extract metrics from import
        nodes = [x for x in imported["@graph"] if x.get("@type") == "kg:Node"]
        edges = [x for x in imported["@graph"] if x.get("@type") == "kg:Edge"]
        sups  = [x for x in imported["@graph"] if x.get("@type") == "kg:Supersession"]

        # Step 4: compare with source graph
        src = load_graph()
        src_nodes = set()
        for e in src.get("edges", []):
            src_nodes.add(e["from"])
            src_nodes.add(e["to"])
        for s in src.get("supersessions", []):
            src_nodes.add(s["from"])
            src_nodes.add(s["target"])

        checks = {
            "node_count_match": len(nodes) == len(src_nodes),
            "edge_count_match": len(edges) == len(src.get("edges", [])),
            "supersession_count_match": len(sups) == len(src.get("supersessions", [])),
            "all_node_ids_unique": len({x["@id"] for x in nodes}) == len(nodes),
            "all_edge_refs_resolve": all(
                any(n["@id"] == ref["@id"] for n in nodes)
                for e in edges for ref in (e.get("source", {}), e.get("target", {})) if ref
            )
        }
        passed = all(checks.values())
        detail = {k: v for k, v in checks.items()}
        detail.update({"imported_nodes": len(nodes), "expected_nodes": len(src_nodes),
                       "imported_edges": len(edges), "expected_edges": len(src.get("edges", []))})
        return passed, detail
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def main():
    if "--verify-roundtrip" in sys.argv:
        ok, detail = verify_roundtrip()
        status = "PASS" if ok else "FAIL"
        print(f"round-trip verification: {status}")
        for k, v in sorted(detail.items()):
            print(f"  {k}: {v}")
        sys.exit(0 if ok else 1)
    else:
        out = "--out" in sys.argv
        path = None
        if out:
            idx = sys.argv.index("--out")
            if idx + 1 < len(sys.argv):
                path = sys.argv[idx + 1]
        export_jsonld(path)

if __name__ == "__main__":
    main()
