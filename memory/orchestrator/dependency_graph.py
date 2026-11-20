#!/usr/bin/env python3
"""Goal Dependency Graph builder - parses memory/goals/*.md, extracts deps, exports JSON.

Usage: python memory/orchestrator/dependency_graph.py [--quiet]
Output: memory/goals/dependency-graph.json (always written)
"""
import os, re, json, sys
from datetime import datetime

AGENT_FILES = {
    'archivist': 'memory/goals/archivist.md',
    'builder': 'memory/goals/builder.md',
    'designer': 'memory/goals/designer.md',
    'mechanic': 'memory/goals/mechanic.md',
    'orchestrator': 'memory/goals/orchestrator.md',
    'researcher': 'memory/goals/researcher.md',
    'scribe': 'memory/goals/scribe.md',
    'verifier': 'memory/goals/verifier.md',
}

def parse_goals():
    goals = []
    for agent, path in AGENT_FILES.items():
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            content = f.read()
        for m in re.finditer(r'^(\d+)\.\s+\*\*(.+?)\*\*\s*-\s*(.+?)(?=^\d+\.|\Z)', content, re.MULTILINE | re.DOTALL):
            num = int(m.group(1))
            title = m.group(2).strip()
            desc = m.group(3).strip()
            verified = 'verified:' in desc.lower() or '(verified' in desc.lower()
            goals.append({
                'id': f'{agent}-{num}',
                'agent': agent,
                'number': num,
                'title': title,
                'description': desc[:500],
                'verified': verified,
            })
    return goals

def extract_dependencies(goals):
    edges = []
    valid_ids = {g['id'] for g in goals}
    def add_edge(src, dst, reason):
        if src != dst:
            edges.append({'from': src, 'to': dst, 'reason': reason.strip()[:150], 'internal': dst in valid_ids})
    for g in goals:
        text = (g['title'] + ' ' + g['description'])
        lt = text.lower()
        for agent in AGENT_FILES:
            if agent == g['agent']:
                continue
            m = re.search(rf'{agent}\s+(?:goal\s+)?#(\d+)', lt)
            if m:
                add_edge(g['id'], f'{agent}-{int(m.group(1))}', f"Depends on {agent.capitalize()} goal #{m.group(1)}")
        m = re.search(r'\(?carried? (?:over )?from\s+([^)]+)\)?', lt)
        if m:
            add_edge(g['id'], f"external:{m.group(1).strip()}", f"Carried from {m.group(1).strip()}")
        m = re.search(r'extend(?:s|ed)?\s+(?:cycle-\d+\s+)?#(\d+)', lt)
        if m:
            add_edge(g['id'], f"external:cycle7-{g['agent']}-{m.group(1)}", f"Extends cycle-7 #{m.group(1)} implementation")
        m = re.search(r'backend done\s+(?:cycle-\d+\s+)?#(\d+)', lt)
        if m:
            add_edge(g['id'], f"external:cycle7-{g['agent']}-{m.group(1)}", f"Backend completed in cycle-7 #{m.group(1)}")
        m = re.search(r'blocked by\s+([a-z]+)\s+#(\d+)', lt)
        if m:
            add_edge(g['id'], f"{m.group(1)}-{int(m.group(2))}", f"Blocked by {m.group(1)}#{m.group(2)}")
        m = re.search(r'(?:requires|needs)\s+(.+?)\s+from\s+([a-z]+)\b', lt)
        if m:
            ta = m.group(2).strip()
            if ta in AGENT_FILES and ta != g['agent']:
                add_edge(g['id'], ta, f"Needs '{m.group(1)[:50]}' from {ta}")
    seen = set()
    unique = []
    for e in edges:
        key = (e['from'], e['to'])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique

def build_graph(goals, edges):
    internal = [e for e in edges if e['internal']]
    external = [e for e in edges if not e['internal']]
    return {
        'generated': datetime.now().isoformat(),
        'cycle': 8,
        'total_goals': len(goals),
        'nodes': [{'id': g['id'], 'agent': g['agent'], 'number': g['number'], 'title': g['title'][:100], 'verified': g['verified']} for g in goals],
        'edges': internal,
        'external_dependencies': external,
        'stats': {'total_goals': len(goals), 'internal_edges': len(internal), 'external_edges': len(external), 'total_dependencies': len(edges), 'agents_with_deps': len(set(e['from'] for e in edges))},
    }

def main():
    quiet = '--quiet' in sys.argv
    goals = parse_goals()
    edges = extract_dependencies(goals)
    graph = build_graph(goals, edges)
    os.makedirs('memory/goals', exist_ok=True)
    out_path = 'memory/goals/dependency-graph.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)
    if not quiet:
        s = graph['stats']
        print(f"Goals: {s['total_goals']} | Internal: {s['internal_edges']} | External: {s['external_edges']} | Total deps: {s['total_dependencies']}")
        print(f"Wrote: {out_path}")
        for e in graph['edges']:
            print(f"  [internal] {e['from']} -> {e['to']}  [{e['reason']}]")

if __name__ == '__main__':
    main()
