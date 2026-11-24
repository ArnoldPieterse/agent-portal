"""Cross-Agent Dependency Graph v2
Builds directed graph of agent goal dependencies from archive.
v2: added file-path cross-references, possessive patterns, known-output mapping.

Output: memory/researcher/dependency-graph.json
"""
import json, re, pathlib, sys
from collections import defaultdict
from datetime import datetime, timezone

ARCHIVE = pathlib.Path("memory/goals/archive")
OUT = pathlib.Path("memory/researcher/dependency-graph.json")

AGENTS = ["archivist", "builder", "designer", "mechanic", "orchestrator", 
          "researcher", "scribe", "verifier"]

# Patterns that indicate a dependency on another agent's work
DEP_PATTERNS = [
    # Explicit: "depends on [agent]", "requires [agent] output"
    (r"(?:depends?\s+on|requires?\s+(?:the\s+)?)([a-z]+)", "explicit_dep"),
    # "from [agent]'s [deliverable]"
    (r"from\s+([a-z]+)[\'\u2019]s", "source_from"),
    # "[agent] output/deliverable/result"
    (r"([a-z]+)\s+(?:output|deliverable|result|metric|index|score|report|graph|model)", "uses_output"),
    # "test the [thing] ([Agent] goal N)" or "([Agent] goal N)"
    (r"\(([A-Z][a-z]+)\s+goal", "refs_goal"),
    # "integrate [agent]'s" 
    (r"integrate\s+([a-z]+)", "integration"),
    # Direct: "[Agent] built/created/wrote/provided"
    (r"([A-Z][a-z]+)\s+(?:built|created|wrote|provided|implemented|generated|computed)", "credit_ref"),
    # Possessive: "[Agent]'s [thing]"
    (r"([A-Z][a-z]+)[\'\u2019]s\s+\w", "possessive"),
    # File path cross-reference: memory/[agent]/
    (r"memory/([a-z]+)/", "file_path_ref"),
    # "[Agent]'s [thing]" lowercase possessive
    (r"([a-z]+)[\'\u2019]s\s+(?:output|result|model|tracker|score|report|metric)", "lower_possessive"),
]

# Known output files mapped to their owner agent
KNOWN_OUTPUTS = {
    "autonomy-score.json": "orchestrator",
    "efficiency-index.jsonl": "researcher",
    "seat-matrix.json": "mechanic",
    "cycle-durations.jsonl": "ops",
    "human-interventions.jsonl": "builder",
    "fleet-mode.json": "orchestrator",
    "convergence-forecast.md": "researcher",
    "dependency-graph.json": "researcher",
    "unavailability-forecast.json": "researcher",
    "topic-evolution.md": "archivist",
    "metric-lineage.md": "archivist",
    "steady-state-playbook.md": "mechanic",
    "convergence-kb.md": "archivist",
    "proposal-quality-baseline.md": "researcher",
    "failure-taxonomy.md": "researcher",
    "cycle_skeleton.py": "orchestrator",
    "goal_ledger.py": "researcher",
    "agent_portal.py": "builder",
    "seat_probe.py": "mechanic",
}

def extract_agent_from_text(text, agent_name):
    """Extract all dependencies from goal text to other agents."""
    deps = []
    seen = set()  # avoid duplicate (target, type) pairs
    
    for pattern, ptype in DEP_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            ref = match.group(1).lower().strip()
            ref = re.sub(r"^\W+|\W+$", "", ref)
            if ref in AGENTS and ref != agent_name and (ref, ptype) not in seen:
                seen.add((ref, ptype))
                deps.append({"target": ref, "type": ptype, "match": match.group(0)[:80]})
    
    # Check for known output file references
    for filename, owner in KNOWN_OUTPUTS.items():
        if owner in AGENTS and owner != agent_name:
            if filename in text.lower() and (owner, "known_output") not in seen:
                seen.add((owner, "known_output"))
                deps.append({"target": owner, "type": "known_output", "match": filename})
    
    return deps

def parse_goal_file(filepath):
    """Parse a goal file, return list of goals with their text."""
    content = filepath.read_text(encoding="utf-8", errors="replace")
    goals = []
    # Try numbered format first
    numbered = re.findall(r"(\d+)\.\s*\*\*(.+?)\*\*\s*-\s*(.+?)(?=\n\d+\.|\n##|\Z)", content, re.DOTALL)
    if numbered:
        for num, name, desc in numbered:
            goals.append({"num": int(num), "name": name.strip(), "text": (name + " - " + desc).strip()[:800]})
    else:
        # Try bullet format: "- **Goal Name**"
        bullets = re.findall(r"-\s*\*\*(.+?)\*\*\s*-?\s*(.+?)(?=\n-|\n##|\Z)", content, re.DOTALL)
        for i, (name, desc) in enumerate(bullets, 1):
            goals.append({"num": i, "name": name.strip(), "text": (name + " - " + desc).strip()[:800]})
    
    return goals

def main():
    if not ARCHIVE.exists():
        print("ERROR: Archive directory not found")
        sys.exit(1)
    
    edges = defaultdict(list)  # cycle -> list of edges
    agent_goal_count = defaultdict(int)
    
    files_processed = 0
    for f in sorted(ARCHIVE.iterdir()):
        if not f.is_file() or not f.name.endswith(".md"):
            continue
        if "SUPERSEDED" in f.name or "test-cycle" in f.name:
            continue
        
        agent = None
        for a in AGENTS:
            if f.name.startswith(a):
                agent = a
                break
        if not agent:
            continue
        
        cycle_match = re.search(r"cycle(\d+)", f.name, re.IGNORECASE)
        cycle = int(cycle_match.group(1)) if cycle_match else 0
        
        goals = parse_goal_file(f)
        agent_goal_count[agent] += len(goals)
        
        for goal in goals:
            deps = extract_agent_from_text(goal["text"], agent)
            for dep in deps:
                edges[cycle].append({
                    "source": agent,
                    "source_goal_num": goal["num"],
                    "source_goal_name": goal["name"][:60],
                    "target": dep["target"],
                    "dep_type": dep["type"],
                })
        
        files_processed += 1
    
    # Identify critical path per cycle (longest chain of dependencies)
    def find_critical_path(cycle_edges):
        if not cycle_edges:
            return []
        adj = defaultdict(set)
        for e in cycle_edges:
            adj[e["source"]].add(e["target"])
        
        best_path = []
        def dfs(node, current_path):
            nonlocal best_path
            if len(current_path) > len(best_path):
                best_path = list(current_path)
            for neighbor in sorted(adj.get(node, set())):
                if neighbor not in current_path:
                    current_path.append(neighbor)
                    dfs(neighbor, current_path)
                    current_path.pop()
        
        for agent in AGENTS:
            if agent in adj:
                dfs(agent, [agent])
        return best_path
    
    critical_paths = {}
    for cycle, cedges in sorted(edges.items()):
        if cedges:
            cp = find_critical_path(cedges)
            if cp:
                critical_paths[str(cycle)] = {
                    "path": cp,
                    "length": len(cp),
                    "edge_count": len(cedges),
                }
    
    total_deps = sum(len(v) for v in edges.values())
    most_depended = defaultdict(int)
    for cedges in edges.values():
        for e in cedges:
            most_depended[e["target"]] += 1
    
    result = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "files_processed": files_processed,
        "total_dependencies_found": total_deps,
        "per_cycle": {},
        "critical_paths": critical_paths,
        "most_depended_on_agents": dict(sorted(most_depended.items(), key=lambda x: -x[1])[:5]),
        "agent_goal_counts": dict(agent_goal_count),
    }
    
    for cycle in sorted(edges.keys())[-5:]:
        cedges = edges[cycle]
        if cedges:
            result["per_cycle"][str(cycle)] = {
                "edge_count": len(cedges),
                "unique_pairs": len(set((e["source"], e["target"]) for e in cedges)),
                "sample_edges": cedges[:5],
            }
    
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    
    print(f"Wrote {OUT}")
    print(f"Files processed: {files_processed}")
    print(f"Total cross-agent dependencies found: {total_deps}")
    print(f"Cycles with dependencies: {len(edges)}")
    print(f"\nMost depended-on agents:")
    for agent, count in sorted(most_depended.items(), key=lambda x: -x[1])[:5]:
        print(f"  {agent}: {count} times referenced")
    print(f"\nCritical paths:")
    for cycle, cp in critical_paths.items():
        path_str = " -> ".join(cp["path"])
        print(f"  Cycle {cycle}: {path_str} (length={cp['length']}, edges={cp['edge_count']})")

if __name__ == "__main__":
    main()
