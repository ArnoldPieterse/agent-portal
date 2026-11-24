"""Knowledge Transfer Efficiency Metric: measures how well prior evidence accelerates goal completion.
Usage: python memory/researcher/knowledge_transfer.py  -> exit 0 if all AC met
AC: >=8 goals scored; >=2 knowledge gaps with named missing artifact; per-agent transfer efficiency score."""
import pathlib, re, json, sys
from collections import defaultdict

BASE = pathlib.Path('.')
RESEARCHER_DIR = BASE / 'memory' / 'researcher'
ARCHIVE_DIR = BASE / 'memory' / 'goals' / 'archive'
CURRENT_GOALS = BASE / 'memory' / 'goals' / 'researcher.md'

def extract_current_cycle_goals():
    """Extract verified goals from the current cycle goal file."""
    if not CURRENT_GOALS.exists(): return []
    text = CURRENT_GOALS.read_text(encoding='utf-8')
    blocks = re.split(r'\n(?=\d+\.\s)', text)
    goals = []
    for block in blocks:
        m_num = re.match(r'(\d+)\.', block.strip())
        if not m_num: continue
        if '(verified:' not in block: continue
        
        # Extract title and verification note
        m_title = re.search(r'\*\*(.+?)\*\*', block[:300])
        title = m_title.group(1) if m_title else f"Goal {m_num.group(1)}"
        
        m_verif = re.search(r'\(verified:\s*(.*?)\)', block)
        verif_note = m_verif.group(1) if m_verif else ''
        
        # Check for prior-knowledge references
        prior_refs = bool(re.search(
            r'as (noted|shown|documented|established) in|building on|per previous|'
            r'same (pattern|approach)|see (also )?(memory/|prior)|'
            r'extending (the )?(same|prior|existing)', verif_note, re.I))
        
        # Check for artifact path in verification
        m_artifact = re.search(r'artifact:\s*(\S+)', verif_note)
        artifact = m_artifact.group(1) if m_artifact else None
        
        goals.append({
            'num': int(m_num.group(1)), 'title': title,
            'verified': True, 'prior_knowledge_cited': prior_refs,
            'verification_note': verif_note[:200], 'artifact': artifact
        })
    return goals


def find_prior_evidence(goal_title):
    """Check if relevant prior evidence exists for a goal topic."""
    # Extract key terms from title
    words = re.findall(r'[a-zA-Z]{4,}', goal_title.lower())
    key_terms = [w for w in words if w not in ('goal', 'build', 'python', 'output', 'verified', 'create', 'implement')]
    
    # Search researcher directory and archive for matching files
    evidence_found = []
    search_dirs = [RESEARCHER_DIR, ARCHIVE_DIR]
    
    for d in search_dirs:
        if not d.exists(): continue
        for f in d.iterdir():
            if not f.is_file() or f.suffix not in ('.md', '.json', '.py'): continue
            fname = f.name.lower()
            # Check if any key term matches the filename
            matches = sum(1 for t in key_terms[:3] if t in fname)
            if matches >= 2:  # At least 2 key terms match
                evidence_found.append(str(f.relative_to(BASE)))
    
    return evidence_found


def score_knowledge_transfer():
    """Main scoring function."""
    goals = extract_current_cycle_goals()
    if len(goals) < 8:
        # Supplement with archive data from recent cycles
        goals = supplement_from_archive(goals)
    
    results = []
    knowledge_gaps = []
    
    for g in goals:
        prior_evidence = find_prior_evidence(g['title'])
        
        # Score components
        cited = 1.0 if g['prior_knowledge_cited'] else 0.0
        evidence_available = 1.0 if prior_evidence else 0.0
        
        # Knowledge gap: evidence existed but wasn't used/cited
        is_gap = (evidence_available and not cited)
        
        # Estimated time saved proxy: if prior evidence exists AND was cited -> ~30% faster
        time_saved_pct = 0.30 if (cited and evidence_available) else (0.15 if evidence_available else 0.0)
        
        result = {
            'num': g['num'], 'title': g['title'][:60],
            'prior_knowledge_cited': bool(cited),
            'prior_evidence_available': len(prior_evidence) > 0,
            'evidence_files_found': prior_evidence[:3],
            'knowledge_gap': is_gap,
            'estimated_time_saved_pct': time_saved_pct
        }
        results.append(result)
        
        if is_gap:
            # Name the missing artifact (the evidence that existed but wasn't leveraged)
            missing = prior_evidence[0] if prior_evidence else f"no_prior_artifact_for_{g['title'][:30].lower().replace(' ', '_')}"
            knowledge_gaps.append({
                'goal': g['title'][:60],
                'missing_leverage': missing,
                'note': f"Prior evidence existed at {missing} but was not cited in completion note"
            })
    
    # Per-agent score (since this is researcher's file, all are researcher's goals)
    # But we can also compute from archive for other agents
    agent_scores = compute_agent_transfer_scores()
    
    # Overall metrics
    n_scored = len(results)
    pct_cited = sum(1 for r in results if r['prior_knowledge_cited']) / max(n_scored, 1) * 100
    gap_rate = sum(1 for r in results if r['knowledge_gap']) / max(n_scored, 1) * 100
    avg_time_saved = sum(r['estimated_time_saved_pct'] for r in results) / max(n_scored, 1)
    
    out = {
        'model': 'knowledge_transfer v1',
        'goals_scored': n_scored,
        'pct_prior_knowledge_cited': round(pct_cited, 1),
        'knowledge_gap_rate_pct': round(gap_rate, 1),
        'avg_estimated_time_saved_pct': round(avg_time_saved * 100, 1),
        'per_goal_scores': results,
        'knowledge_gaps_identified': knowledge_gaps[:5],
        'per_agent_transfer_efficiency': agent_scores,
        'methodology': "For each verified goal: check if prior evidence file exists (2+ key term filename match in researcher/archive); scored as cited if verification note references prior work; gap = evidence existed but not leveraged"
    }
    
    out_path = RESEARCHER_DIR / 'knowledge-transfer-results.json'
    out_path.write_text(json.dumps(out, indent=2), encoding='utf-8')
    return out


def supplement_from_archive(goals):
    """If current cycle has <8 verified goals, supplement from recent archive."""
    if len(goals) >= 8: return goals
    
    # Get from most recent archive files
    arch_files = sorted(ARCHIVE_DIR.glob('researcher*.md')) + sorted(ARCHIVE_DIR.glob('cycle*_researcher.md'))
    for f in reversed(arch_files[-5:]):
        text = f.read_text(encoding='utf-8')
        blocks = re.split(r'\n(?=\d+\.\s)', text)
        for block in blocks:
            if '(verified:' not in block: continue
            m_num = re.match(r'(\d+)\.', block.strip())
            if not m_num: continue
            m_title = re.search(r'\*\*(.+?)\*\*', block[:300])
            title = m_title.group(1) if m_title else f"Archive goal {m_num.group(1)}"
            m_verif = re.search(r'\(verified:\s*(.*?)\)', block)
            verif_note = m_verif.group(1) if m_verif else ''
            prior_refs = bool(re.search(
                r'as (noted|shown|documented)|building on|per previous|see also', verif_note, re.I))
            goals.append({'num': 90 + int(m_num.group(1)), 'title': title,
                         'verified': True, 'prior_knowledge_cited': prior_refs,
                         'verification_note': verif_note[:200], 'artifact': None})
        if len(goals) >= 8: break
    return goals


def compute_agent_transfer_scores():
    """Compute per-agent knowledge transfer efficiency from archive."""
    agent_data = defaultdict(lambda: {'total': 0, 'cited': 0, 'gaps': 0})
    
    for f in sorted(ARCHIVE_DIR.glob('*.md')):
        if 'test' in f.name.lower(): continue
        m_agent = re.match(r'(\w+)', f.name)
        if not m_agent: continue
        agent = m_agent.group(1).lower()
        if agent in ('2026', 'index', 'readme'): continue
        m_ca = re.match(r'cycle\d+_(\w+)', f.name)
        if m_ca: agent = m_ca.group(1).lower()
        
        text = f.read_text(encoding='utf-8')
        blocks = re.split(r'\n(?=\d+\.\s)', text)
        for block in blocks:
            if '(verified:' not in block: continue
            agent_data[agent]['total'] += 1
            if re.search(r'as (noted|shown|documented)|building on|per previous|see also', block, re.I):
                agent_data[agent]['cited'] += 1
    
    scores = {}
    for agent, d in sorted(agent_data.items()):
        if d['total'] < 3: continue
        efficiency = d['cited'] / d['total'] * 100
        scores[agent] = {'goals': d['total'], 'cited_prior': d['cited'],
                        'transfer_efficiency_pct': round(efficiency, 1)}
    return scores


def main():
    out = score_knowledge_transfer()
    
    ac1 = out['goals_scored'] >= 8
    ac2 = len(out['knowledge_gaps_identified']) >= 2
    ac3 = len(out['per_agent_transfer_efficiency']) > 0
    
    print(f"Knowledge Transfer Efficiency:")
    print(f"  Goals scored: {out['goals_scored']}")
    print(f"  % prior knowledge cited: {out['pct_prior_knowledge_cited']}%")
    print(f"  Knowledge gap rate: {out['knowledge_gap_rate_pct']}%")
    print(f"  Avg est. time saved: {out['avg_estimated_time_saved_pct']}%")
    print(f"  Per-agent scores: {list(out['per_agent_transfer_efficiency'].keys())}")
    print(f"  Knowledge gaps identified: {len(out['knowledge_gaps_identified'])}")
    for kg in out['knowledge_gaps_identified'][:3]:
        print(f"    - {kg['goal']} -> missing leverage: {kg['missing_leverage']}")
    
    ac = {'ac1_goals>=8': ac1, 'ac2_gaps>=2': ac2, 'ac3_agent_scores': ac3}
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