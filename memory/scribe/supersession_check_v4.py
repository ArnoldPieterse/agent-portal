#!/usr/bin/env python3
"""supersession_check_v4.py - Fixed matcher: full-path resolution + strict canonical pattern.

Fixes over v3:
1. 'canonical' marker now requires \bcanonical\s*[:=] (word boundary + required = or :)
   - Eliminates false positives from filenames containing "canonical" (e.g. synthesis-index-canonical-r61-...)
2. Target resolution: bare filenames resolved via source-dir-relative, root-relative, and basename-glob
3. Only flags as truly broken if NO resolution strategy finds the file

Exit codes: 0 = healthy (zero true dangling refs), 1 = violations, 2 = error
"""
import json, re, sys, os
from pathlib import Path
from collections import defaultdict
from datetime import datetime

MARKER_PATTERNS = [
    (re.compile(r'supersedes\s+([\w/\\.\-]+\.md)', re.I), 'supersedes'),
    (re.compile(r'SUPERSEDED.*?see\s+[`]?([\w/\\.\-]+\.md)[`]?', re.I), 'see'),
    (re.compile(r'superseded by\s+[`]?([\w/\\.\-]+\.md)[`]?', re.I), 'superseded_by'),
    # FIXED: require word boundary + mandatory = or : after "canonical"
    (re.compile(r'\bcanonical\s*[:=]\s*[`]?([\w/\\.\-/]+\.md)[`]?', re.I), 'canonical'),
]

def extract_edges(root: Path):
    edges = []
    superseded_set = set()
    for f in root.rglob("*.md"):
        rel = str(f).replace(os.sep, "/")
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        first_lines = "\n".join(text.splitlines()[:5])
        if re.search(r'SUPERSEDED|superseded', first_lines, re.I):
            superseded_set.add(rel)
        for i, line in enumerate(text.splitlines(), 1):
            for pattern, mtype in MARKER_PATTERNS:
                for m in pattern.finditer(line):
                    target_raw = m.group(1).lstrip("./")
                    if not target_raw.startswith("memory/") and "/" in target_raw:
                        target_raw = "memory/" + target_raw
                    edges.append({"source": rel, "target": target_raw, "marker": mtype, "line": i})
    return edges, superseded_set

def resolve_target(target, source_rel, root):
    """Try multiple resolution strategies. Returns resolved path or None."""
    candidates = [
        root / target,
        root / target.replace("memory/", "", 1),
    ]
    src_dir = (root / source_rel).parent
    candidates.append(src_dir / target)
    if not target.startswith("memory/"):
        candidates.append(root / "memory" / target)
    for c in candidates:
        if c.exists():
            return str(c.relative_to(root)).replace(os.sep, "/")
    basename = Path(target).name
    matches = list(root.rglob(basename))
    if len(matches) == 1:
        return str(matches[0].relative_to(root)).replace(os.sep, "/")
    return None

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()
    
    root = Path(args.root)
    mem_root = root / "memory"
    if not mem_root.exists():
        print(json.dumps({"error": "memory/ not found"}))
        sys.exit(2)
    
    edges, superseded_set = extract_edges(mem_root)
    
    truly_broken = []
    resolved_count = 0
    for e in edges:
        resolved = resolve_target(e["target"], e["source"], root)
        if resolved:
            resolved_count += 1
        else:
            truly_broken.append(e)
    
    # Build graph with resolved targets for head/cycle analysis
    adj = defaultdict(list)
    all_nodes = set()
    for e in edges:
        resolved = resolve_target(e["target"], e["source"], root)
        target_node = resolved if resolved else e["target"]
        adj[e["source"]].append(target_node)
        all_nodes.add(e["source"])
        all_nodes.add(target_node)
    
    # Cycle detection (iterative to avoid recursion limit)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = defaultdict(int)
    cycles = []
    for start in list(adj.keys()):
        if color[start] != WHITE:
            continue
        stack = [(start, iter(adj.get(start, [])))]
        color[start] = GRAY
        path = [start]
        while stack:
            node, it = stack[-1]
            advanced = False
            for neighbor in it:
                if color[neighbor] == GRAY:
                    idx = path.index(neighbor) if neighbor in path else -1
                    if idx >= 0:
                        cycles.append(path[idx:] + [neighbor])
                elif color[neighbor] == WHITE:
                    color[neighbor] = GRAY
                    stack.append((neighbor, iter(adj.get(neighbor, []))))
                    path.append(neighbor)
                    advanced = True
                    break
            if not advanced:
                color[node] = BLACK
                stack.pop()
                path.pop()
    
    # Heads and orphans
    sources = set(adj.keys())
    targets_set = set()
    for e in edges:
        resolved = resolve_target(e["target"], e["source"], root)
        targets_set.add(resolved if resolved else e["target"])
    
    heads = sorted(n for n in all_nodes if n in sources and n not in superseded_set)
    orphaned = sorted(n for n in superseded_set if n not in targets_set)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "v4",
        "total_leaves_scanned": sum(1 for _ in mem_root.rglob("*.md")),
        "supersession_edges": len(edges),
        "superseded_files_marked": len(superseded_set),
        "edges_resolved": resolved_count,
        "truly_broken_chains": len(truly_broken),
        "truly_broken_entries": truly_broken,
        "cycles_detected": len(cycles),
        "orphaned_superseded": orphaned,
        "canonical_heads_count": len(heads),
        "healthy": len(truly_broken) == 0 and len(cycles) == 0,
    }
    
    report_path = mem_root / "scribe" / "supersession-report-v4.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    if not args.quiet:
        print(json.dumps({k: v for k, v in report.items() if k != "truly_broken_entries"}, indent=2))
        if truly_broken:
            print(f"\nTruly broken ({len(truly_broken)}):")
            for e in truly_broken[:20]:
                print(f"  {e['source']}:{e['line']} -> {e['target']} ({e['marker']})")
    
    sys.exit(0 if report["healthy"] else 1)

if __name__ == "__main__":
    main()
