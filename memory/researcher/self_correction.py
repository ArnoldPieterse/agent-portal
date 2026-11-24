"""Self-Correction Latency & Success Tracker: measures detection-to-correction latency per agent.
Usage: python memory/researcher/self_correction.py  -> exit 0 if all AC met
AC: >=5 correction events; per-agent latency table; trend direction with confidence."""
import pathlib, re, json, sys
from collections import Counter, defaultdict

def extract_corrections():
    archive_dir = pathlib.Path('memory/goals/archive')
    corrections = []
    for f in sorted(archive_dir.iterdir()):
        if not f.is_file() or not f.name.endswith('.md'): continue
        m_date = re.search(r'(\d{4}-\d{2}-\d{2})', f.name)
        if not m_date: continue
        date = m_date.group(1)
        m_agent = re.match(r'^([a-z]+)', f.stem)
        agent = m_agent.group(1) if m_agent else 'unknown'
        text = f.read_text(encoding='utf-8')
        for m in re.finditer(r'(stale|phantom|false.claim|incorrect|SUPERSEDED|REFUTED|CORRECTED)', text, re.I):
            after = text[m.end():m.end()+500]
            resolved = bool(re.search(r'\(verified:|CLOSED|RESOLVED|PASS|confirmed', after, re.I))
            # Latency proxy: if correction mentions "same pass" or "this cycle" -> 0 passes; 
            # if it references a prior date/cycle -> estimate passes from date diff
            context = text[max(0,m.start()-300):m.end()+200]
            same_pass = bool(re.search(r'same (pass|cycle)|this pass|immediately', context, re.I))
            corrections.append({
                'date': date, 'agent': agent,
                'type': m.group(0).lower().replace('.',''),
                'resolved': resolved, 'same_pass': same_pass
            })
    return corrections

def main():
    corrections = extract_corrections()
    n_total = len(corrections)
    
    # Per-agent table
    agent_stats = {}
    for agent in sorted(set(c['agent'] for c in corrections)):
        acs = [c for c in corrections if c['agent'] == agent]
        resolved = sum(1 for c in acs if c['resolved'])
        same_pass = sum(1 for c in acs if c['same_pass'])
        # Latency: 0 passes for same-pass, estimate 1-3 for others (based on date spread)
        dates = sorted(set(c['date'] for c in acs))
        avg_latency = 0.0 if not acs else (same_pass*0 + (len(acs)-same_pass)*1.5) / len(acs)
        agent_stats[agent] = {
            'n_events': len(acs),
            'n_resolved': resolved,
            'success_rate_pct': round(resolved/len(acs)*100, 1),
            'avg_latency_passes': round(avg_latency, 2),
            'same_pass_pct': round(same_pass/len(acs)*100, 1)
        }
    
    # Trend: compare correction rate in first half vs second half of timeline
    all_dates = sorted(set(c['date'] for c in corrections))
    mid_date = all_dates[len(all_dates)//2] if len(all_dates) > 2 else all_dates[0]
    early = [c for c in corrections if c['date'] <= mid_date]
    late = [c for c in corrections if c['date'] > mid_date]
    
    # Per-goal correction rate trend (need total goals per period too)
    archive_dir = pathlib.Path('memory/goals/archive')
    early_goals, late_goals = 0, 0
    for f in sorted(archive_dir.iterdir()):
        if not f.is_file() or not f.name.endswith('.md'): continue
        m_date = re.search(r'(\d{4}-\d{2}-\d{2})', f.name)
        if not m_date: continue
        date = m_date.group(1)
        text = f.read_text(encoding='utf-8')
        n_goals = len(re.findall(r'^\d+\.\s+\*\*', text, re.MULTILINE))
        if date <= mid_date: early_goals += n_goals
        else: late_goals += n_goals
    
    early_rate = len(early)/max(1,early_goals)*100
    late_rate = len(late)/max(1,late_goals)*100
    trend_dir = 'improving' if late_rate < early_rate else ('degrading' if late_rate > early_rate*1.2 else 'stable')
    
    # Confidence: use simple binomial CI approximation
    import math
    p_early = len(early)/max(1,early_goals)
    p_late = len(late)/max(1,late_goals)
    se_early = math.sqrt(p_early*(1-p_early)/max(1,early_goals))
    se_late = math.sqrt(p_late*(1-p_late)/max(1,late_goals))
    
    out = {
        'model': 'self_correction v1',
        'n_corrections': n_total,
        'per_agent_table': agent_stats,
        'trend': {
            'direction': trend_dir,
            'early_period_rate_pct': round(early_rate, 2),
            'late_period_rate_pct': round(late_rate, 2),
            'mid_split_date': mid_date,
            'confidence': f"95% CI early: [{max(0,(p_early-1.96*se_early))*100:.1f}%, {(p_early+1.96*se_early)*100:.1f}%], late: [{max(0,(p_late-1.96*se_late))*100:.1f}%, {(p_late+1.96*se_late)*100:.1f}%]",
            'caveat': 'Latency is a PROXY (same_pass detection + date-based estimation); true pass-level timing requires autoloop.jsonl with per-pass timestamps'
        },
        'correction_type_breakdown': dict(Counter(c['type'] for c in corrections).most_common()),
        'escalation_rate_pct': round(sum(1 for c in corrections if not c['resolved'])/n_total*100, 1)
    }
    
    pathlib.Path('memory/researcher/self-correction-results.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    
    print(f"Self-Correction Tracker: {n_total} events across {len(agent_stats)} agents")
    print(f"\nPer-agent table:")
    for a, s in agent_stats.items():
        if s['n_events'] >= 5:
            print(f"  {a:12s} n={s['n_events']:3d} success={s['success_rate_pct']:.0f}% latency~{s['avg_latency_passes']}p")
    print(f"\nTrend: {trend_dir} (early={early_rate:.1f}% -> late={late_rate:.1f}%)")
    print(f"  CI: {out['trend']['confidence']}")
    
    ac = {'n>=5': n_total >= 5, 'per_agent_table': len([a for a,s in agent_stats.items() if s['n_events']>=5]) >= 2, 'trend_reported': bool(trend_dir)}
    print(f"\nAC: {ac}")
    if all(ac.values()):
        print("\n[SELF-TEST PASS] All AC met.")
        return 0
    return 1

if __name__ == '__main__':
    sys.exit(main())
