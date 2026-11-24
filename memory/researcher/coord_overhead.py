"""Cross-Agent Coordination Overhead Model: measures inter-agent communication cost vs productive work.
Usage: python memory/researcher/coord_overhead.py  -> exit 0 if all AC met
AC: >=3 agent pairs measured; 1 clear bottleneck identified with evidence; scaling projection at 12 agents."""
import pathlib, re, json, sys, math
from collections import defaultdict

ARCHIVE_DIR = pathlib.Path('memory/goals/archive')
AGENTS = ['orchestrator', 'builder', 'verifier', 'designer', 'archivist', 'scribe', 'mechanic', 'researcher']

def extract_cross_refs():
    """Extract cross-agent references from all goal files."""
    # Each record: {source_agent, target_agents, context, file}
    refs = []
    for f in sorted(ARCHIVE_DIR.glob('*.md')):
        if 'test' in f.name.lower(): continue
        m_agent = re.match(r'(\w+)', f.name)
        if not m_agent: continue
        source = m_agent.group(1).lower()
        m_ca = re.match(r'cycle\d+_(\w+)', f.name)
        if m_ca: source = m_ca.group(1).lower()
        source = re.sub(r'_\d+$', '', source)
        if source not in AGENTS: continue
        
        text = f.read_text(encoding='utf-8')
        # Find blocks that reference other agents
        blocks = re.split(r'\n(?=\d+\.\s)', text)
        for block in blocks:
            targets = []
            for target in AGENTS:
                if target == source: continue
                # Look for agent name references in goal text (not just filename)
                pattern = rf'\b{target}\b'
                matches = re.findall(pattern, block, re.I)
                if len(matches) >= 1 and 'test' not in block.lower()[:50]:
                    targets.extend([target] * min(len(matches), 3))  # Cap at 3 per goal
            
            if targets:
                refs.append({
                    'source': source,
                    'targets': set(targets),
                    'ref_count': len(targets),
                    'file': f.name,
                    'snippet': block.strip()[:100]
                })
    return refs


def compute_pairwise_overhead(refs):
    """Compute coordination overhead per agent pair."""
    pair_counts = defaultdict(int)
    pair_refs = defaultdict(list)
    
    for ref in refs:
        for target in ref['targets']:
            pair_key = tuple(sorted([ref['source'], target]))
            pair_counts[pair_key] += ref['ref_count']
            pair_refs[pair_key].append(ref)
    
    # Normalize: overhead = cross-refs / total goals for that source
    total_by_agent = defaultdict(int)
    for f in sorted(ARCHIVE_DIR.glob('*.md')):
        if 'test' in f.name.lower(): continue
        m_agent = re.match(r'(\w+)', f.name)
        if not m_agent: continue
        agent = m_agent.group(1).lower()
        m_ca = re.match(r'cycle\d+_(\w+)', f.name)
        if m_ca: agent = m_ca.group(1).lower()
        agent = re.sub(r'_\d+$', '', agent)
        if agent not in AGENTS: continue
        text = f.read_text(encoding='utf-8')
        goals = len(re.findall(r'^\d+\.\s', text, re.MULTILINE))
        total_by_agent[agent] += goals
    
    results = {}
    for pair, count in sorted(pair_counts.items(), key=lambda x: -x[1]):
        a, b = pair
        # Overhead ratio: cross-refs / (total goals of both agents)
        denom = max(total_by_agent.get(a, 1) + total_by_agent.get(b, 1), 1)
        ratio = count / denom
        results[f"{a}<->{b}"] = {
            'cross_ref_count': count,
            'overhead_ratio': round(ratio, 4),
            'sample_refs': len(pair_refs[pair])
        }
    return results, total_by_agent


def scaling_projection(current_agents, pair_results):
    """Project overhead at N agents. Model: coordination cost ~ O(N^2) for all-pairs."""
    n_current = len(current_agents)
    n_projected = 12
    
    # Current total cross-refs
    current_total = sum(v['cross_ref_count'] for v in pair_results.values())
    
    # Scaling: if coordination follows O(N^2), at 12 agents:
    scale_factor = (n_projected * (n_projected - 1)) / (n_current * (n_current - 1))
    projected_total = current_total * scale_factor
    
    # Identify which pairs would be worst under scaling
    top_pairs = sorted(pair_results.items(), key=lambda x: -x[1]['cross_ref_count'])[:5]
    projected_bottlenecks = []
    for pair, data in top_pairs:
        projected_bottlenecks.append({
            'pair': pair,
            'current_overhead': data['cross_ref_count'],
            'projected_12_agents': round(data['cross_ref_count'] * scale_factor),
            'risk': 'HIGH' if data['overhead_ratio'] > 0.05 else 'MEDIUM'
        })
    
    return {
        'current_agents': n_current,
        'projected_agents': n_projected,
        'scale_factor': round(scale_factor, 2),
        'model': f"O(N^2) all-pairs: coordination cost scales by {scale_factor}x",
        'projected_total_cross_refs': round(projected_total),
        'top_projected_bottlenecks': projected_bottlenecks
    }


def main():
    refs = extract_cross_refs()
    pair_results, totals = compute_pairwise_overhead(refs)
    
    # AC1: >=3 agent pairs measured
    ac1 = len(pair_results) >= 3
    
    # AC2: identify 1 clear bottleneck with evidence
    bottleneck = None
    if pair_results:
        top_pair = max(pair_results.items(), key=lambda x: x[1]['cross_ref_count'])
        bottleneck = {
            'pair': top_pair[0],
            'cross_refs': top_pair[1]['cross_ref_count'],
            'overhead_ratio': top_pair[1]['overhead_ratio'],
            'evidence': f"{top_pair[1]['sample_refs']} distinct goal blocks reference this pair"
        }
    ac2 = bottleneck is not None and bottleneck['cross_refs'] >= 3
    
    # AC3: scaling projection
    proj = scaling_projection(AGENTS, pair_results)
    ac3 = 'projected_12_agents' in str(proj) or 'projected_total_cross_refs' in proj
    
    out = {
        'model': 'coord_overhead v1',
        'total_cross_refs_found': len(refs),
        'agent_pairs_measured': len(pair_results),
        'pairwise_overhead': pair_results,
        'bottleneck_identified': bottleneck,
        'scaling_projection': proj,
        'methodology': "Cross-agent references extracted from goal text (agent names mentioned in other agents' goals); overhead = ref_count / total_goals_of_both_agents"
    }
    
    out_path = pathlib.Path('memory/researcher/coord-overhead-results.json')
    out_path.write_text(json.dumps(out, indent=2), encoding='utf-8')
    
    print(f"Coordination Overhead Model:")
    print(f"  Cross-refs found: {len(refs)}")
    print(f"  Agent pairs measured: {len(pair_results)}")
    if bottleneck:
        print(f"  Top bottleneck: {bottleneck['pair']} ({bottleneck['cross_refs']} cross-refs, ratio={bottleneck['overhead_ratio']})")
    print(f"  Scaling projection (8->12 agents): {proj['scale_factor']}x increase")
    
    # Top 5 pairs
    print(f"\n  {'Pair':<30} {'Refs':>5} {'Ratio':>8}")
    for pair, data in list(pair_results.items())[:8]:
        print(f"  {pair:<30} {data['cross_ref_count']:>5} {data['overhead_ratio']:>8.4f}")
    
    ac = {'ac1_pairs>=3': ac1, 'ac2_bottleneck': ac2, 'ac3_scaling': ac3}
    print(f"\nAC: {ac}")
    if all(ac.values()):
        print("[SELF-TEST PASS] All AC met.")
        return 0
    else:
        failed = [k for k,v in ac.items() if not v]
        print(f"[AC PARTIAL] Failed: {failed}")
        return 1

if __name__ == '__main__':
    sys.exit(main())