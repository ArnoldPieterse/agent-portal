"""
Cross-Agent Implicit Dependency Sequencer
===========================================
Discovers implicit behavioral dependencies from cycle history (evidence + handoffs),
builds a DAG, and produces optimal dispatch order via topological sort.

Usage:
  python memory/builder/implicit_sequencer.py --selftest    # synthetic data test
  python memory/builder/implicit_sequencer.py --run         # analyze real history
  python memory/builder/implicit_sequencer.py --show        # display current dispatch_order.json
"""
import json, sys, os, re
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict, deque

BASE = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = BASE / "memory"
DISPATCH_ORDER_FILE = BASE / "memory" / "goals" / "dispatch_order.json"
AGENT_NAMES = ["orchestrator", "builder", "verifier", "designer", "mechanic", "researcher", "scribe", "archivist"]

# ─── Dependency Discovery ─────────────────────────────────────────────────────

def discover_dependencies(evidence_files):
    """
    Parse evidence/handoff files to find implicit dependencies.
    A dependency edge (A -> B) means B's work depends on A's output,
    so A must be dispatched before B.
    
    Heuristics:
    1. Handoff files: "from X to Y" = X before Y
    2. Evidence mentioning another agent's output as prerequisite
    3. Pattern: agent B references agent A's artifact in their goal/evidence
    """
    # edges: set of (prerequisite_agent, dependent_agent)
    edges = set()
    
    for fpath in evidence_files:
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        
        # Pattern 1: handoff "from X to Y" or "X -> Y"
        for match in re.finditer(r'(?:handoff|from)\s+([a-z]+).{0,20}?(?:to|->)\s+([a-z]+)', content, re.IGNORECASE):
            src, dst = match.group(1).lower(), match.group(2).lower()
            if src in AGENT_NAMES and dst in AGENT_NAMES:
                edges.add((src, dst))
        
        # Pattern 2: "after X completes" or "depends on X"
        for match in re.finditer(r'(?:after|depends\s+on|waits\s+for)\s+([a-z]+)', content, re.IGNORECASE):
            dep = match.group(1).lower()
            if dep in AGENT_NAMES:
                # Determine which agent this file belongs to
                owner = _file_owner(fpath)
                if owner and owner != dep:
                    edges.add((dep, owner))
        
        # Pattern 3: "X output feeds Y" or "X result consumed by Y"
        for match in re.finditer(r'([a-z]+)\s+(?:output|result|test|build).{0,20}?(?:feeds|consumed\s+by|used\s+by)\s+([a-z]+)', content, re.IGNORECASE):
            src, dst = match.group(1).lower(), match.group(2).lower()
            if src in AGENT_NAMES and dst in AGENT_NAMES:
                edges.add((src, dst))
        
        # Pattern 4: evidence file owned by agent X mentions agent Y by name
        owner = _file_owner(fpath)
        if owner:
            text_lower = content.lower()
            for other in AGENT_NAMES:
                if other != owner and other in text_lower:
                    edges.add((other, owner))
    
    return edges

def _file_owner(fpath):
    """Determine which agent owns a file based on path."""
    parts = fpath.parts
    for p in parts:
        if p.lower() in AGENT_NAMES:
            return p.lower()
    return None

# ─── DAG + Topological Sort ──────────────────────────────────────────────────

def build_dag(edges, agents):
    """Build adjacency list from edge set. Returns (adj, in_degree)."""
    adj = defaultdict(list)
    in_degree = {a: 0 for a in agents}
    for src, dst in edges:
        if src in agents and dst in agents and src != dst:
            adj[src].append(dst)
            in_degree[dst] += 1
    return adj, in_degree

def topological_sort(agents, adj, in_degree):
    """Kahn's algorithm. Returns ordered list or None if cycle detected."""
    queue = deque([a for a in agents if in_degree[a] == 0])
    order = []
    while queue:
        # Prefer deterministic ordering (alphabetical among ready nodes)
        queue = deque(sorted(queue))
        node = queue.popleft()
        order.append(node)
        for neighbor in sorted(adj[node]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    if len(order) != len(agents):
        return None  # cycle detected
    return order

# ─── Rationale Generation ────────────────────────────────────────────────────

def generate_rationale(order, edges):
    """For each agent in the order, explain why it's placed there."""
    edge_list = list(edges)
    rationale = []
    for i, agent in enumerate(order):
        # What must complete before this agent?
        prereqs = [src for src, dst in edge_list if dst == agent]
        # What does this agent unblock?
        unblocks = [dst for src, dst in edge_list if src == agent]
        
        reasons = []
        if prereqs:
            reasons.append(f"depends on: {', '.join(sorted(prereqs))}")
        else:
            reasons.append("no prerequisites (can start immediately)")
        if unblocks:
            reasons.append(f"unblocks: {', '.join(sorted(unblocks))}")
        
        rationale.append({
            "position": i + 1,
            "agent": agent,
            "reason": "; ".join(reasons)
        })
    return rationale

# ─── Core Logic ──────────────────────────────────────────────────────────────

def sequence(agents=None, edges=None):
    """Main entry: discover deps, build DAG, topo-sort, write output."""
    if agents is None:
        agents = AGENT_NAMES[:]
    
    if edges is None:
        # Discover from real files
        evidence_files = list(EVIDENCE_DIR.rglob("evidence*.md")) + list(EVIDENCE_DIR.rglob("handoff*.md"))
        edges = discover_dependencies(evidence_files)
    
    adj, in_degree = build_dag(edges, agents)
    order = topological_sort(agents, adj, in_degree)
    
    if order is None:
        # Cycle detected - fall back to alphabetical
        print("  WARNING: cycle detected in dependency graph, using alphabetical fallback")
        order = sorted(agents)
    
    rationale = generate_rationale(order, edges)
    
    result = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "order": order,
        "edges": [list(e) for e in sorted(edges)],
        "rationale": rationale,
        "agents_count": len(agents),
        "constraints_count": len(edges)
    }
    
    return result

def write_dispatch_order(result):
    DISPATCH_ORDER_FILE.parent.mkdir(parents=True, exist_ok=True)
    DISPATCH_ORDER_FILE.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return DISPATCH_ORDER_FILE

# ─── Selftest ────────────────────────────────────────────────────────────────

def cmd_selftest():
    print("  Running implicit_sequencer selftest...")
    results = []
    
    # Test 1: Dependency discovery from synthetic handoffs
    import tempfile, shutil
    tmpdir = Path(tempfile.mkdtemp())
    try:
        # Create synthetic evidence files
        (tmpdir / "memory" / "builder").mkdir(parents=True)
        (tmpdir / "memory" / "verifier").mkdir(parents=True)
        (tmpdir / "memory" / "designer").mkdir(parents=True)
        (tmpdir / "memory" / "handoffs").mkdir(parents=True)
        
        # Handoff: builder -> verifier
        (tmpdir / "memory" / "handoffs" / "builder-to-verifier.md").write_text(
            "# Handoff\nFrom builder to verifier. Test suite is ready for validation.", encoding="utf-8"
        )
        # Evidence: designer depends on builder
        (tmpdir / "memory" / "designer" / "evidence-ui-build.md").write_text(
            "# UI Build\nThis work is after builder completes the API endpoints.", encoding="utf-8"
        )
        # Evidence: verifier depends on builder  
        (tmpdir / "memory" / "verifier" / "evidence-test-run.md").write_text(
            "# Test Run\nDepends on builder test suite. Verifies all outputs.", encoding="utf-8"
        )
        
        evidence_files = list(tmpdir.rglob("*.md"))
        edges = discover_dependencies(evidence_files)
        
        # Verify we found the expected edges
        assert ("builder", "verifier") in edges, f"Missing builder->verifier edge. Got: {edges}"
        assert ("builder", "designer") in edges, f"Missing builder->designer edge. Got: {edges}"
        results.append(("dependency_discovery", True, f"found {len(edges)} edges"))
        
        # Test 2: Topological sort correctness
        agents = ["orchestrator", "builder", "verifier", "designer", "mechanic"]
        test_edges = {("builder", "verifier"), ("builder", "designer"), ("verifier", "mechanic")}
        adj, in_degree = build_dag(test_edges, agents)
        order = topological_sort(agents, adj, in_degree)
        
        assert order is not None, "Topo sort returned None (cycle?)"
        assert len(order) == 5, f"Expected 5 agents, got {len(order)}"
        # builder must come before verifier and designer
        assert order.index("builder") < order.index("verifier"), "builder must precede verifier"
        assert order.index("builder") < order.index("designer"), "builder must precede designer"
        # verifier must come before mechanic
        assert order.index("verifier") < order.index("mechanic"), "verifier must precede mechanic"
        results.append(("topological_sort", True, f"order: {order}"))
        
        # Test 3: Cycle detection
        cycle_edges = {("a", "b"), ("b", "c"), ("c", "a")}
        agents_c = ["a", "b", "c"]
        adj_c, in_deg_c = build_dag(cycle_edges, agents_c)
        order_c = topological_sort(agents_c, adj_c, in_deg_c)
        assert order_c is None, f"Cycle should return None, got {order_c}"
        results.append(("cycle_detection", True, "correctly detected cycle"))
        
        # Test 4: Full sequence() + dispatch_order.json validity
        result = sequence(agents=agents, edges=test_edges)
        assert "order" in result and len(result["order"]) == 5
        assert "rationale" in result and len(result["rationale"]) == 5
        assert all(r["agent"] in agents for r in result["rationale"])
        
        # Write and validate JSON
        test_output = tmpdir / "dispatch_order.json"
        DISPATCH_ORDER_FILE_ORIG = DISPATCH_ORDER_FILE
        global _test_dispatch_file
        _test_dispatch_file = test_output
        
        # Write to temp location for selftest
        test_output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        loaded = json.loads(test_output.read_text(encoding="utf-8"))
        assert loaded["agents_count"] == 5
        assert loaded["constraints_count"] == 3
        assert all(isinstance(r["position"], int) for r in loaded["rationale"])
        results.append(("dispatch_order_json", True, "valid JSON with correct schema"))
        
        # Test 5: Rationale completeness
        for r in result["rationale"]:
            assert "reason" in r and len(r["reason"]) > 0
            assert "position" in r and 1 <= r["position"] <= 5
        results.append(("rationale_complete", True, f"{len(result['rationale'])} entries with reasons"))
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    # Summary
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    for name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name}: {detail}")
    print(f"\n  SELFTEST: {passed}/{total} PASS")
    
    return passed == total

# ─── CLI Commands ────────────────────────────────────────────────────────────

def cmd_run():
    result = sequence()
    path = write_dispatch_order(result)
    print(f"  Dispatch order written to: {path.relative_to(BASE)}")
    for r in result["rationale"]:
        print(f"    {r['position']}. {r['agent']} - {r['reason']}")
    return True

def cmd_show():
    if not DISPATCH_ORDER_FILE.exists():
        print("  No dispatch_order.json found. Run --run first.")
        return False
    data = json.loads(DISPATCH_ORDER_FILE.read_text(encoding="utf-8"))
    print(f"  Generated: {data['generated']}")
    print(f"  Agents: {data['agents_count']}, Constraints: {data['constraints_count']}")
    for r in data["rationale"]:
        print(f"    {r['position']}. {r['agent']} - {r['reason']}")
    return True

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0
    cmd = args[0].lstrip("-")
    if cmd == "selftest":
        ok = cmd_selftest()
        return 0 if ok else 1
    elif cmd == "run":
        ok = cmd_run()
        return 0 if ok else 1
    elif cmd == "show":
        ok = cmd_show()
        return 0 if ok else 1
    else:
        print(f"Unknown command: {args[0]}")
        print(__doc__)
        return 1

if __name__ == "__main__":
    sys.exit(main())
