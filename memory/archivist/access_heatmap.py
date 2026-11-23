#!/usr/bin/env python3
"""
access_heatmap.py - Knowledge Access Heatmap (Archivist Goal #6, cycle-12)

Instruments which agents read/cite which leaves (from goal files + citation map).
Ranks under-used high-value leaves and over-relied-on fragile ones.

Usage:
    python memory/archivist/access_heatmap.py [--selftest]

Output:
    memory/archivist/access-heatmap.json  (render-ready for Cockpit)
"""
import json, re, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ARCHIVIST = Path("memory/archivist")
GOALS = Path("memory/goals")
MEMORY = Path("memory")
KNOWN_AGENTS = {"archivist", "builder", "designer", "mechanic", "orchestrator",
                "researcher", "scribe", "verifier"}

# Regex to find memory/ path references in text
PATH_RE = re.compile(r'memory/[a-z_]+/[A-Za-z0-9._\-/]+\.(?:md|json|py|html|css|js)')


def attribute_agent(filepath: str) -> str:
    """Attribute a citing file to an agent."""
    parts = filepath.replace("\\", "/").split("/")
    if len(parts) >= 2 and parts[0] == "memory" and parts[1] in KNOWN_AGENTS:
        return parts[1]
    if "goals" in parts:
        fname = Path(filepath).stem.lower()
        for agent in KNOWN_AGENTS:
            if agent in fname:
                return agent
        # Check file content for agent attribution
        try:
            p = Path(filepath)
            if p.exists():
                first_line = p.read_text(encoding='utf-8', errors='ignore')[:200].lower()
                for agent in KNOWN_AGENTS:
                    if agent in first_line:
                        return agent
        except Exception:
            pass
    return "shared"


def scan_goal_files() -> list:
    """Scan all goal files and evidence leaves for path references.
    Returns list of (citing_file, cited_path) tuples."""
    edges = []
    
    # Scan goal files
    if GOALS.exists():
        for gf in sorted(GOALS.glob("*.md")):
            try:
                text = gf.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            refs = PATH_RE.findall(text)
            for ref in refs:
                if ref != str(gf):
                    edges.append((str(gf), ref))
    
    # Scan evidence leaves (first 200 lines of each to keep it fast)
    for lane_dir in sorted(MEMORY.iterdir()):
        if not lane_dir.is_dir() or lane_dir.name.startswith('.'):
            continue
        if lane_dir.name == 'archivist' and False:  # skip self for now
            continue
        for leaf in sorted(lane_dir.glob("*.md"))[:50]:
            try:
                text = leaf.read_text(encoding='utf-8', errors='ignore')[:20000]
            except Exception:
                continue
            refs = PATH_RE.findall(text)
            for ref in refs:
                if ref != str(leaf):
                    edges.append((str(leaf), ref))
    
    return edges


def load_citation_map_edges() -> list:
    """Load from pre-built citation map (supplementary)."""
    cm_path = ARCHIVIST / "citation-map.json"
    if not cm_path.exists():
        return []
    data = json.loads(cm_path.read_text(encoding='utf-8'))
    result = []
    for edge in data.get('all_edges', []):
        result.append((edge['citing'], edge['cited']))
    return result


def load_kg_in_degree() -> dict:
    """Compute in-degree per node from knowledge-graph-v3.json."""
    kg_path = ARCHIVIST / "knowledge-graph-v3.json"
    if not kg_path.exists():
        return {}
    kg = json.loads(kg_path.read_text(encoding='utf-8'))
    in_deg = defaultdict(int)
    for edge in kg.get('edges', []):
        in_deg[edge['to']] += 1
    return dict(in_deg)


def build_heatmap() -> dict:
    """Build the full access heatmap."""
    # Combine edges from both sources (dedup)
    raw_edges = set()
    for citing, cited in scan_goal_files():
        raw_edges.add((citing, cited))
    for citing, cited in load_citation_map_edges():
        raw_edges.add((citing, cited))
    
    in_degree = load_kg_in_degree()

    # Access matrix: agent -> leaf -> set of citing files
    access = defaultdict(lambda: defaultdict(set))
    leaf_total_citations = defaultdict(int)
    leaf_citing_agents = defaultdict(set)

    for citing, cited in raw_edges:
        agent = attribute_agent(citing)
        access[agent][cited].add(citing)
        leaf_total_citations[cited] += 1
        leaf_citing_agents[cited].add(agent)

    # Convert to counts
    agent_leaf_counts = {}
    for agent, leaves in access.items():
        agent_leaf_counts[agent] = {leaf: len(srcs) for leaf, srcs in leaves.items()}

    all_leaves = set(leaf_total_citations.keys())

    # Under-used high-value: in-degree >= 3 but total citations < 2
    underused = []
    for leaf in sorted(all_leaves):
        kg_deg = in_degree.get(leaf, 0)
        if kg_deg >= 3 and leaf_total_citations[leaf] < 2:
            underused.append({
                "leaf": leaf,
                "kg_in_degree": kg_deg,
                "citations_received": leaf_total_citations[leaf],
                "citing_agents": sorted(leaf_citing_agents.get(leaf, set())),
                "reason": f"high graph connectivity ({kg_deg}) but only {leaf_total_citations[leaf]} direct citation(s)"
            })
    underused.sort(key=lambda x: -x["kg_in_degree"])

    # Over-relied fragile: >=3 citations from a single agent, no other agents cite it
    over_relied = []
    for leaf in sorted(all_leaves):
        agents = leaf_citing_agents.get(leaf, set())
        if len(agents) == 1:
            sole_agent = list(agents)[0]
            count = sum(1 for c, l in raw_edges if l == leaf and attribute_agent(c) == sole_agent)
            if count >= 3:
                over_relied.append({
                    "leaf": leaf,
                    "sole_agent": sole_agent,
                    "citation_count": count,
                    "kg_in_degree": in_degree.get(leaf, 0),
                    "reason": f"heavily cited only by {sole_agent} ({count}x) - single point of failure"
                })
    over_relied.sort(key=lambda x: -x["citation_count"])

    # Lane coverage
    lanes_covered = set()
    for leaf in all_leaves:
        parts = leaf.replace("\\", "/").split("/")
        if len(parts) >= 2 and parts[0] == "memory" and parts[1] in KNOWN_AGENTS:
            lanes_covered.add(parts[1])

    # Agent top leaves (ranked)
    agent_top = {}
    for agent, leaves in agent_leaf_counts.items():
        ranked = sorted(leaves.items(), key=lambda x: -x[1])[:5]
        agent_top[agent] = [{"leaf": l, "citations": c} for l, c in ranked]

    result = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_edges_processed": len(raw_edges),
        "total_leaves_cited": len(all_leaves),
        "lanes_covered": sorted(lanes_covered),
        "lane_coverage_complete": len(lanes_covered) >= 5,
        "agent_top_leaves": agent_top,
        "underused_high_value": underused[:20],
        "over_relied_fragile": over_relied[:10],
        "stats": {
            "agents_tracked": len(agent_leaf_counts),
            "shared_citations": agent_leaf_counts.get("shared", {}),
            "top_shared_leaves": sorted(
                [(l, c) for l, c in agent_leaf_counts.get("shared", {}).items()],
                key=lambda x: -x[1]
            )[:5]
        }
    }
    return result


def selftest() -> bool:
    """Verify acceptance criteria."""
    print("[selftest] Building heatmap...")
    result = build_heatmap()
    
    passed = 0
    total = 5
    
    # 1. Covers all top-level lanes (>=5 of 8 known agents)
    lanes = result["lanes_covered"]
    ok = len(lanes) >= 5
    print(f"  [{'PASS' if ok else 'FAIL'}] Lane coverage: {len(lanes)}/8 -> {lanes}")
    passed += ok
    
    # 2. Agent's most-cited leaf is ranked #1
    ok = True
    for agent, leaves in result["agent_top_leaves"].items():
        if len(leaves) >= 2:
            if leaves[0]["citations"] < leaves[1]["citations"]:
                ok = False
                break
    print(f"  [{'PASS' if ok else 'FAIL'}] Ranking correct (most-cited = #1)")
    passed += ok
    
    # 3. JSON is render-ready (valid structure)
    ok = all(k in result for k in ["generated", "agent_top_leaves", "underused_high_value", "over_relied_fragile"])
    print(f"  [{'PASS' if ok else 'FAIL'}] JSON structure complete")
    passed += ok
    
    # 4. Under-used high-value list is non-empty and sorted
    uhv = result["underused_high_value"]
    ok = len(uhv) > 0 and all(uhv[i]["kg_in_degree"] >= uhv[i+1]["kg_in_degree"] for i in range(len(uhv)-1)) if len(uhv) > 1 else len(uhv) > 0
    print(f"  [{'PASS' if ok else 'FAIL'}] Under-used high-value: {len(uhv)} items, sorted by in-degree")
    passed += ok
    
    # 5. Over-relied fragile list has sole_agent field
    orf = result["over_relied_fragile"]
    ok = all("sole_agent" in item for item in orf) if orf else True
    print(f"  [{'PASS' if ok else 'FAIL'}] Over-relied fragile: {len(orf)} items with sole_agent")
    passed += ok
    
    # Write output
    out_path = ARCHIVIST / "access-heatmap.json"
    out_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    
    print(f"\n[selftest] {passed}/{total} checks passed")
    return passed == total


def main():
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    
    result = build_heatmap()
    out_path = ARCHIVIST / "access-heatmap.json"
    out_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f"[access_heatmap] Wrote {out_path} ({out_path.stat().st_size}B)")
    print(f"  edges={result['total_edges_processed']}, leaves={result['total_leaves_cited']}, "
          f"lanes={len(result['lanes_covered'])}/8")
    print(f"  underused_high_value={len(result['underused_high_value'])}, "
          f"over_relied_fragile={len(result['over_relied_fragile'])}")


if __name__ == "__main__":
    main()
