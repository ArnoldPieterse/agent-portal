#!/usr/bin/env python3
"""Cross-Agent Dependency Resolver (Orchestrator goal #6).
Parses memory/goals/*.md for cross-agent references, builds a directed graph,
detects cycles + orphaned deps. Writes JSON to memory/orchestrator/dependency-graph.json.
Usage: python memory/orchestrator/dependency_resolver.py [--check]
  --check: exit 0 if no cycles, exit 1 if cycles found
"""
import json, re, sys
from pathlib import Path

GOALS_DIR = Path("memory/goals")
AGENTS = ["orchestrator","researcher","builder","verifier","designer","archivist","scribe","mechanic"]
AGENT_PAT = "|".join(AGENTS)
REF_RE = re.compile(r"\b(" + AGENT_PAT + r")['’]?(?:\s*goal\s*)?#(\d{1,2})\b", re.I)

def parse_goals():
    nodes = {}
    edges = []
    all_files = sorted(GOALS_DIR.glob("*.md")) + sorted(GOALS_DIR.rglob("*.md"))
    seen = set()
    for f in all_files:
        if str(f) in seen:
            continue
        seen.add(str(f))
        agent = f.stem.lower()
        is_agent_file = agent in AGENTS
        content = f.read_text(errors="replace")
        lines = content.splitlines()
        if is_agent_file:
            self_goals = set(int(m) for m in re.findall(r"^\s*(\d{1,2})[\.\)]", content, re.M))
            nodes[agent] = {"goals": sorted(self_goals), "file": str(f)}
        # Scan ALL files (agent + non-agent) for cross-references
        for i, line in enumerate(lines):
            for m in REF_RE.finditer(line):
                ref_agent = m.group(1).lower()
                ref_num = int(m.group(2))
                src_id = f"{agent}#{ref_num}" if is_agent_file else f"file:{f.stem}"
                tgt_id = f"{ref_agent}#{ref_num}"
                edges.append({"from": src_id, "to": tgt_id, "file": str(f), "line": i+1, "context": line.strip()[:100]})
    return nodes, edges

def build_adj(edges):
    adj = {}
    for e in edges:
        adj.setdefault(e["from"], set()).add(e["to"])
    return adj

def detect_cycles(adj):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in adj}
    cycles = []
    def dfs(node, path):
        color[node] = GRAY
        path.append(node)
        for nxt in sorted(adj.get(node, [])):
            if nxt not in color:
                color[nxt] = WHITE
            if color[nxt] == GRAY:
                idx = path.index(nxt)
                cycles.append(path[idx:] + [nxt])
            elif color[nxt] == WHITE:
                dfs(nxt, path)
        path.pop()
        color[node] = BLACK
    for n in sorted(adj):
        if color.get(n, WHITE) == WHITE:
            dfs(n, [])
    return cycles

def find_orphans(nodes, edges):
    """Goals that are referenced but don't exist in the target agent's goal list."""
    orphans = []
    all_targets = set(e["to"] for e in edges)
    for ref in all_targets:
        agent, num = ref.rsplit("#", 1)
        num = int(num)
        if agent in nodes and num not in nodes[agent]["goals"]:
            orphans.append({"ref": ref, "reason": f"{agent} goal #{num} not found in {nodes[agent]['file']}"})
    return orphans

def main():
    check_only = "--check" in sys.argv
    nodes, edges = parse_goals()
    real_edges = [e for e in edges if e["from"] != e["to"]]
    adj = build_adj(real_edges)
    cycles = detect_cycles(adj)
    orphans = find_orphans(nodes, edges)
    result = {"nodes": nodes, "edges": edges, "cycles": cycles, "orphans": orphans, "stats": {"agents": len(nodes), "edges": len(edges), "cycles": len(cycles), "orphans": len(orphans)}}
    if not check_only:
        out = Path("memory/orchestrator/dependency-graph.json")
        out.write_text(json.dumps(result, indent=2))
        print(f"Wrote {out}: {len(nodes)} agents, {len(edges)} edges, {len(cycles)} cycles, {len(orphans)} orphans")
    if cycles:
        print("CYCLES DETECTED:")
        for c in cycles[:5]:
            print(f"  {' -> '.join(c)}")
    if orphans:
        print(f"ORPHANED REFS ({len(orphans)}):")
        for o in orphans[:10]:
            print(f"  {o['ref']}: {o['reason']}")
    sys.exit(1 if cycles else 0)

if __name__ == "__main__":
    main()
