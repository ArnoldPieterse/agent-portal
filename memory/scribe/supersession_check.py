#!/usr/bin/env python3
"""supersession_check.py - Scribe#5 policy owner: supersession-chain integrity validator.

Scans memory/ for explicit supersession markers, builds the directed graph, and checks:
  1. Acyclic (no cycles)
  2. No broken chains (every "supersedes X" target exists on disk)
  3. Canonical head unambiguous per topic (exactly one non-superseded leaf per chain)
  4. Chain depth <= 4 hops (flag deeper chains for consolidation)

Usage:
  python memory/scribe/supersession_check.py [--root .] [--quiet]

Exit codes: 0 = healthy, 1 = violations found, 2 = error
Output: JSON report to stdout + writes memory/scribe/supersession-report.json
"""
import json, re, sys, os
from pathlib import Path
from collections import defaultdict, deque
from datetime import datetime

# --- Marker patterns (ordered by specificity) ---
MARKER_PATTERNS = [
    # "supersedes <path>" or "SUPERSEDED ... see <path>"
    (re.compile(r'supersedes\s+([\w/\\.\-]+\.md)', re.I), 'supersedes'),
    (re.compile(r'SUPERSEDED.*?see\s+[`]?([\w/\\.\-]+\.md)[`]?', re.I), 'see'),
    (re.compile(r'superseded by\s+[`]?([\w/\\.\-]+\.md)[`]?', re.I), 'superseded_by'),
    # "canonical = <path>" style
    (re.compile(r'canonical\s*=?\s*[`]?([\w/\\.\-]+\.md)[`]?', re.I), 'canonical'),
]

def extract_edges(root: Path):
    """Walk all .md files, find supersession markers, return edge list."""
    edges = []       # (source_file, target_file, marker_type, line_no)
    superseded_set = set()  # files explicitly marked as superseded
    
    for f in root.rglob("*.md"):
        rel = str(f).replace(os.sep, "/")
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        
        # Check if this file is marked as superseded (in its own header/title)
        first_lines = "\n".join(text.splitlines()[:5])
        if re.search(r'SUPERSEDED|superseded', first_lines, re.I):
            superseded_set.add(rel)
        
        for i, line in enumerate(text.splitlines(), 1):
            for pattern, mtype in MARKER_PATTERNS:
                for m in pattern.finditer(line):
                    target_raw = m.group(1)
                    # Normalize path: strip leading memory/ if present, ensure relative
                    target = target_raw.lstrip("./")
                    if not target.startswith("memory/") and "/" in target:
                        target = "memory/" + target
                    elif not target.startswith("memory/"):
                        # might be a bare filename - try to resolve
                        target = target  # leave as-is, will fail existence check
                    edges.append({
                        "source": rel,
                        "target": target,
                        "marker": mtype,
                        "line": i
                    })
    return edges, superseded_set

def build_graph(edges):
    """Build adjacency list: source -> [targets] (source supersedes targets)."""
    adj = defaultdict(list)
    all_nodes = set()
    for e in edges:
        adj[e["source"]].append(e["target"])
        all_nodes.add(e["source"])
        all_nodes.add(e["target"])
    return adj, all_nodes

def detect_cycles(adj):
    """DFS cycle detection. Returns list of cycles found."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = defaultdict(int)
    parent = {}
    cycles = []
    
    def dfs(node, path):
        color[node] = GRAY
        path.append(node)
        for neighbor in adj.get(node, []):
            if color[neighbor] == GRAY:
                # Found cycle - extract it
                idx = path.index(neighbor)
                cycles.append(path[idx:] + [neighbor])
            elif color[neighbor] == WHITE:
                dfs(neighbor, path)
        path.pop()
        color[node] = BLACK
    
    for node in list(adj.keys()):
        if color[node] == WHITE:
            dfs(node, [])
    return cycles

def check_broken_chains(edges, root):
    """Check that every target in an edge exists on disk."""
    broken = []
    for e in edges:
        target_path = root / e["target"]
        if not target_path.exists():
            # Try without memory/ prefix
            alt = root / e["target"].replace("memory/", "", 1)
            if not alt.exists():
                broken.append(e)
    return broken

def find_heads(adj, all_nodes, superseded_set, edges):
    """Find canonical heads and orphaned superseded nodes."""
    # A head is a node that supersedes others but is itself not marked superseded
    sources = set(adj.keys())  # nodes that supersede something
    targets = set(e["target"] for e in edges)  # nodes that are superseded by something

    heads = []
    for node in all_nodes:
        if node in sources and node not in superseded_set:
            heads.append(node)

    # Orphaned: marked superseded but no edge points to them (no successor recorded)
    orphaned = []
    for node in superseded_set:
        if node not in targets:
            orphaned.append(node)

    return sorted(heads), sorted(orphaned)


def detect_cycles(adj):
    """DFS cycle detection. Returns list of cycles found."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = defaultdict(int)
    parent = {}
    cycles = []
    
    def dfs(node, path):
        color[node] = GRAY
        path.append(node)
        for neighbor in adj.get(node, []):
            if color[neighbor] == GRAY:
                # Found cycle - extract it
                idx = path.index(neighbor)
                cycles.append(path[idx:] + [neighbor])
            elif color[neighbor] == WHITE:
                dfs(neighbor, path)
        path.pop()
        color[node] = BLACK
    
    for node in list(adj.keys()):
        if color[node] == WHITE:
            dfs(node, [])
    return cycles

def check_broken_chains(edges, root):
    """Check that every target in an edge exists on disk."""
    broken = []
    for e in edges:
        target_path = root / e["target"]
        if not target_path.exists():
            # Try without memory/ prefix
            alt = root / e["target"].replace("memory/", "", 1)
            if not alt.exists():
                broken.append(e)
    return broken

def compute_chain_depths(adj):
    """Compute longest chain from each node (BFS/DFS)."""
    memo = {}
    def depth(node, visiting=None):
        if visiting is None:
            visiting = set()
        if node in memo:
            return memo[node]
        if node in visiting:
            return 0  # cycle guard
        visiting.add(node)
        max_d = 0
        for child in adj.get(node, []):
            d = 1 + depth(child, visiting)
            max_d = max(max_d, d)
        visiting.discard(node)
        memo[node] = max_d
        return max_d
    
    depths = {}
    for node in list(adj.keys()):
        depths[node] = depth(node)
    return depths

def main():
    import argparse
    p = argparse.ArgumentParser(description="Supersession chain integrity validator")
    p.add_argument("--root", default=".", help="Root directory")
    p.add_argument("--quiet", action="store_true", help="Exit code only, no output")
    args = p.parse_args()
    
    root = Path(args.root)
    mem_root = root / "memory"
    
    if not mem_root.exists():
        print(json.dumps({"error": f"memory/ not found under {root}"}))
        sys.exit(2)
    
    edges, superseded_set = extract_edges(mem_root)
    adj, all_nodes = build_graph(edges)
    cycles = detect_cycles(adj)
    broken = check_broken_chains(edges, root)
    heads, orphaned = find_heads(adj, all_nodes, superseded_set, edges)
    depths = compute_chain_depths(adj)
    
    deep_chains = {k: v for k, v in depths.items() if v > 4}
    
    # Unambiguous head check: for each chain, exactly one head
    # Group by connected component
    components = defaultdict(set)
    def find_component(node):
        visited = set()
        stack = [node]
        while stack:
            n = stack.pop()
            if n in visited:
                continue
            visited.add(n)
            for child in adj.get(n, []):
                stack.append(child)
        return visited
    
    # Simplified: check that no two heads claim to be canonical for the same topic
    # (approximation: if two heads have overlapping targets, flag it)
    head_target_overlap = []
    for i, h1 in enumerate(heads):
        t1 = set(adj.get(h1, []))
        for h2 in heads[i+1:]:
            t2 = set(adj.get(h2, []))
            overlap = t1 & t2
            if overlap:
                head_target_overlap.append({"head1": h1, "head2": h2, "overlap": list(overlap)})
    
    violations = {
        "cycles": len(cycles),
        "broken_chains": len(broken),
        "orphaned_superseded": len(orphaned),
        "deep_chains_gt4": len(deep_chains),
        "head_target_overlaps": len(head_target_overlap),
    }
    
    healthy = all(v == 0 for v in violations.values())
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "root": str(root),
        "total_leaves_scanned": sum(1 for _ in mem_root.rglob("*.md")),
        "supersession_edges": len(edges),
        "superseded_files_marked": len(superseded_set),
        "cycles_detected": len(cycles),
        "broken_chains": len(broken),
        "orphaned_superseded": orphaned,
        "canonical_heads": heads,
        "deep_chains_gt4": deep_chains,
        "head_target_overlaps": head_target_overlap,
        "healthy": healthy,
        "violations": violations,
    }
    
    # Write report
    report_path = mem_root / "scribe" / "supersession-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    if not args.quiet:
        print(json.dumps(report, indent=2))
    
    sys.exit(0 if healthy else 1)

if __name__ == "__main__":
    main()
