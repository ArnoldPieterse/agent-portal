#!/usr/bin/env python3
"""KG Integrity Report - Archivist Goal #1 (cycle-5)
Produces: total nodes, edge count, orphan count, dangling ref count, cycle detection.
Writes to memory/archivist/kg-report-cycle5.md
"""
import json, os, sys
from collections import defaultdict
from datetime import date

def kg_integrity():
    with open("memory/archivist/knowledge_graph.json", "r") as f:
        kg = json.load(f)
    
    edges = kg.get("edges", [])
    supersessions = kg.get("supersessions", [])
    
    # Collect all nodes
    nodes = set()
    for e in edges:
        nodes.add(e["from"])
        nodes.add(e["to"])
    for s in supersessions:
        if isinstance(s, dict):
            nodes.add(s.get("from", ""))
            nodes.add(s.get("to", ""))
        elif isinstance(s, (list, tuple)) and len(s) >= 2:
            nodes.add(s[0])
            nodes.add(s[1])
    nodes = {n for n in nodes if n}
    
    total_nodes = len(nodes)
    total_edges = len(edges) + len(supersessions)
    
    # Inbound edges per node
    inbound = defaultdict(int)
    for e in edges:
        inbound[e["to"]] += 1
    for s in supersessions:
        if isinstance(s, dict):
            inbound[s.get("to", "")] += 1
        elif isinstance(s, (list, tuple)) and len(s) >= 2:
            inbound[s[1]] += 1
    
    # Orphans: nodes with no inbound edges
    orphans = sorted([n for n in nodes if inbound[n] == 0])
    orphan_count = len(orphans)

    # Actionable orphans: exclude intentionally-standalone nodes from the
    # remediation allowlist (cycle-5 goal #4). A fresh run without this would
    # report all 154; the true needs-link count is what goal #4 tracks.
    allowlist_path = os.path.join(os.path.dirname(__file__), "orphan-allowlist.json")
    allowed = set()
    if os.path.exists(allowlist_path):
        with open(allowlist_path, "r", encoding="utf-8") as af:
            allowed = set(json.load(af).get("standalone", []))
    actionable_orphans = sorted([o for o in orphans if o not in allowed])
    actionable_orphan_count = len(actionable_orphans)
    
    # Dangling references: edge targets that don't exist on disk
    dangling = []
    for e in edges:
        if not os.path.exists(e["to"]):
            dangling.append({"edge": e, "missing": e["to"]})
    for s in supersessions:
        target = s.get("to") if isinstance(s, dict) else (s[1] if isinstance(s, (list, tuple)) and len(s) >= 2 else None)
        if target and not os.path.exists(target):
            dangling.append({"edge": s, "missing": target})
    dangling_count = len(dangling)
    
    # Cycle detection (DFS)
    adj = defaultdict(list)
    for e in edges:
        adj[e["from"]].append(e["to"])
    for s in supersessions:
        if isinstance(s, dict):
            adj[s.get("from", "")].append(s.get("to", ""))
        elif isinstance(s, (list, tuple)) and len(s) >= 2:
            adj[s[0]].append(s[1])
    
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}
    cycles = []
    
    def dfs(node, path):
        color[node] = GRAY
        path.append(node)
        for neighbor in adj.get(node, []):
            if neighbor not in color:
                continue
            if color[neighbor] == GRAY:
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
            elif color[neighbor] == WHITE:
                dfs(neighbor, path)
        path.pop()
        color[node] = BLACK
    
    for n in list(nodes):
        if color[n] == WHITE:
            dfs(n, [])
    
    cycle_count = len(cycles)
    
    return {
        "total_nodes": total_nodes,
        "edge_count": total_edges,
        "orphan_count": orphan_count,
        "actionable_orphan_count": actionable_orphan_count,
        "standalone_allowlist_size": len(allowed),
        "dangling_ref_count": dangling_count,
        "cycle_count": cycle_count,
        "cycles_sample": cycles[:5],
        "orphans_sample": orphans[:10],
        "dangling_sample": dangling[:5]
    }

def write_report(result):
    today = date.today().isoformat()
    lines = [
        f"# KG Integrity Report - Cycle 5",
        f"Generated: {today}",
        f"Source: memory/archivist/knowledge_graph.json",
        f"",
        f"## Metrics",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total nodes | {result['total_nodes']} |",
        f"| Edge count (pointers + supersessions) | {result['edge_count']} |",
        f"| Orphan count (no inbound edges) | {result['orphan_count']} |",
        f"| Actionable orphans (excl. standalone allowlist) | {result.get('actionable_orphan_count', 'n/a')} |",
        f"| Standalone allowlist size | {result.get('standalone_allowlist_size', 'n/a')} |",
        f"| Dangling reference count | {result['dangling_ref_count']} |",
        f"| Cycle count | {result['cycle_count']} |",
        f"",
        f"## Orphans (sample of 10)",
    ]
    for o in result["orphans_sample"]:
        lines.append(f"- `{o}`")
    
    if result["dangling_sample"]:
        lines.append(f"\n## Dangling References (sample)")
        for d in result["dangling_sample"]:
            lines.append(f"- missing: `{d['missing']}`")
    
    if result["cycles_sample"]:
        lines.append(f"\n## Cycles Detected")
        for c in result["cycles_sample"]:
            lines.append(f"- {' -> '.join(c)}")
    else:
        lines.append(f"\n## Cycles: None detected")
    
    lines.append(f"\n---")
    lines.append(f"*Generated by kg_integrity.py (Scribe assist for Archivist goal #1)*")
    
    out_path = "memory/archivist/kg-report-cycle5.md"
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    return out_path

if __name__ == "__main__":
    result = kg_integrity()
    print(json.dumps(result, indent=2))
    out = write_report(result)
    print(f"\nReport written to: {out}")
