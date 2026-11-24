"""Autonomous Decision Quality Differential: compares quality of human-directed vs self-selected goals.
Usage: python memory/researcher/decision_quality_diff.py  -> exit 0 if all AC met
AC: >=2 agents with n>=5 per cohort; >=1 agent with p<0.1 on any metric; caveats included."""
import pathlib, re, json, sys, math
from collections import defaultdict

ARCHIVE_DIR = pathlib.Path('memory/goals/archive')
EARLY_CUTOFF = '2026-11-16'  # Fleet setup period: human was actively directing

def classify_cohort(block_text, date):
    """Classify a goal as A (human-influenced) or B (autonomous/self-selected).
    
    Heuristic: Early cycle goals (<= EARLY_CUTOFF) were set during active human setup.
    Later goals come from auto-loop where agents self-select from their queue.
    Strong text markers can override the temporal default."""
    strong_human = bool(re.search(
        r'user (said|directed|requested|asked|told|wants)|human (directive|requested)'
        r'|"fix the |"change to |"add |"remove ', block_text, re.I))
    strong_auto = bool(re.search(
        r'auto-?loop|idle.?time|self-?select', block_text, re.I))
    
    if strong_human: return 'A'
    if strong_auto: return 'B'
    return 'A' if date <= EARLY_CUTOFF else 'B'


def parse_goals():
    """Parse all archive files into structured goal records."""
    goals = []
    for f in sorted(ARCHIVE_DIR.glob('*.md')):
        if not f.is_file() or 'test' in f.name.lower():
            continue
        m_date = re.search(r'(\d{4}-\d{2}-\d{2})', f.name)
        if not m_date: continue
        date = m_date.group(1)
        
        m_agent = re.match(r'(\w+)', f.name)
        agent = m_agent.group(1).lower() if m_agent else 'unknown'
        if agent in ('2026', 'index', 'readme', 'rosterprobe'): continue
        # Strip cycle prefix: "cycle14_researcher" -> "researcher"
        m_cycle_agent = re.match(r'cycle\d+_(\w+)', f.name)
        if m_cycle_agent: agent = m_cycle_agent.group(1).lower()
        # Strip suffixes like "_15"
        agent = re.sub(r'_\d+$', '', agent)
        
        text = f.read_text(encoding='utf-8')
        blocks = re.split(r'\n(?=\d+\.\s)', text)
        for block in blocks:
            if not re.match(r'\d+\.', block.strip()): continue
            verified = '(verified:' in block or 'reached' in block.lower()[:200]
            
            # Quality signals
            corrections = len(re.findall(
                r're-?verif|corrected|after revision|retry|supersed|rework|incorrect|phantom', block, re.I))
            
            # Specificity proxy: longer goals with file paths = more specific
            has_path = bool(re.search(r'memory/\w+/', block[:400]))
            goal_len = len(block.strip())
            
            cohort = classify_cohort(block, date)
            
            goals.append({
                'agent': agent, 'date': date, 'verified': verified,
                'corrections': corrections, 'cohort': cohort,
                'has_path': has_path, 'goal_len': goal_len,
                'first_pass': corrections == 0
            })
    return goals


def welch_t(x, y):
    """Welch's t-test. Returns (t_stat, p_approx)."""
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2: return 0.0, 1.0
    mx, my = sum(x)/nx, sum(y)/ny
    vx = sum((xi-mx)**2 for xi in x)/(nx-1)
    vy = sum((yi-my)**2 for yi in y)/(ny-1)
    se = math.sqrt(vx/nx + vy/ny)
    if se == 0: return 0.0, 1.0
    t = (mx - my) / se
    # Welch-Satterthwaite df
    num = (vx/nx + vy/ny)**2
    den_a = (vx/nx)**2/(nx-1) if nx > 1 else 0
    den_b = (vy/ny)**2/(ny-1) if ny > 1 else 0
    df = num/(den_a+den_b) if (den_a+den_b) > 0 else nx+ny-2
    abs_t = abs(t)
    # Approximate p (normal for large df, conservative t for small)
    if df >= 30:
        p = 2.0 * (1 - 0.5*(1 + math.erf(abs_t/math.sqrt(2))))
    else:
        p = min(1.0, 2.0 * math.exp(-0.7 * abs_t**1.5))
    return t, max(p, 1e-6)


def main():
    goals = parse_goals()
    verified = [g for g in goals if g['verified']]
    
    print(f"Total parsed: {len(goals)}, Verified: {len(verified)}")
    
    # Per-agent analysis
    agents = sorted(set(g['agent'] for g in verified))
    agent_results = {}
    all_significant = []
    
    for agent in agents:
        a_data = [g for g in verified if g['cohort'] == 'A' and g['agent'] == agent]
        b_data = [g for g in verified if g['cohort'] == 'B' and g['agent'] == agent]
        
        if len(a_data) < 3 or len(b_data) < 3:
            continue
        
        # Metric 1: First-pass acceptance (no correction markers)
        a_fp = [float(g['first_pass']) for g in a_data]
        b_fp = [float(g['first_pass']) for g in b_data]
        t_fp, p_fp = welch_t(a_fp, b_fp)
        
        # Metric 2: Correction count (lower is better)
        a_corr = [float(g['corrections']) for g in a_data]
        b_corr = [float(g['corrections']) for g in b_data]
        t_c, p_c = welch_t(a_corr, b_corr)
        
        # Metric 3: Specificity proxy (has file path reference)
        a_spec = [float(g['has_path']) for g in a_data]
        b_spec = [float(g['has_path']) for g in b_data]
        t_s, p_s = welch_t(a_spec, b_spec)
        
        r = {
            'n_a': len(a_data), 'n_b': len(b_data),
            'first_pass_acceptance': {
                'A': round(sum(a_fp)/len(a_fp), 3), 'B': round(sum(b_fp)/len(b_fp), 3),
                'delta_B_minus_A': round(sum(b_fp)/len(b_fp) - sum(a_fp)/len(a_fp), 3),
                't': round(t_fp, 3), 'p': round(p_fp, 4)
            },
            'correction_count': {
                'A_mean': round(sum(a_corr)/len(a_corr), 3), 'B_mean': round(sum(b_corr)/len(b_corr), 3),
                'delta_B_minus_A': round(sum(b_corr)/len(b_corr) - sum(a_corr)/len(a_corr), 3),
                't': round(t_c, 3), 'p': round(p_c, 4)
            },
            'specificity_rate': {
                'A': round(sum(a_spec)/len(a_spec), 3), 'B': round(sum(b_spec)/len(b_spec), 3),
                'delta_B_minus_A': round(sum(b_spec)/len(b_spec) - sum(a_spec)/len(a_spec), 3),
                't': round(t_s, 3), 'p': round(p_s, 4)
            }
        }
        agent_results[agent] = r
        
        for metric in ['first_pass_acceptance', 'correction_count', 'specificity_rate']:
            if r[metric]['p'] < 0.1:
                all_significant.append({'agent': agent, 'metric': metric, 'p': r[metric]['p'],
                                        'delta': r[metric]['delta_B_minus_A']})
    
    # AC checks
    sufficient = {a: r for a, r in agent_results.items() if r['n_a'] >= 5 and r['n_b'] >= 5}
    ac1 = len(sufficient) >= 2
    ac2 = len(all_significant) >= 1
    
    out = {
        'model': 'decision_quality_diff v1',
        'classification_method': f"Temporal: date<={EARLY_CUTOFF}=A(human), later=B(autonomous); text markers override",
        'total_goals': len(goals), 'verified_goals': len(verified),
        'cohort_sizes': {'A_human_influenced': sum(1 for g in verified if g['cohort']=='A'),
                         'B_autonomous': sum(1 for g in verified if g['cohort']=='B')},
        'per_agent': agent_results,
        'agents_sufficient_n>=5_per_cohort': list(sufficient.keys()),
        'significant_findings': all_significant,
        'caveats': [
            'Cohort A/B split is temporal (early setup vs later auto-loop), not per-goal human attribution',
            'Early goals were set during active human fleet construction; later goals from autonomous queue selection',
            'First-pass acceptance proxied by absence of correction text markers (4.9% of all goals have any)',
            'Small correction signal makes p-values sensitive to a few outlier goals',
            'Temporal confound: early goals may differ in type/scope from later autonomous goals, not just direction',
        ]
    }
    
    out_path = pathlib.Path('memory/researcher/decision-quality-results.json')
    out_path.write_text(json.dumps(out, indent=2), encoding='utf-8')
    
    print(f"\nCohort sizes: A={out['cohort_sizes']['A_human_influenced']}, B={out['cohort_sizes']['B_autonomous']}")
    print(f"Agents with n>=5 per cohort: {list(sufficient.keys())}")
    print(f"Significant findings (p<0.1): {len(all_significant)}")
    for s in all_significant[:5]:
        print(f"  {s['agent']} / {s['metric']}: p={s['p']:.3f}, Δ(B-A)={s['delta']:+.3f}")
    
    # Print summary table
    print(f"\n{'Agent':<12} {'nA':>4} {'nB':>4} {'FP_A':>6} {'FP_B':>6} {'Δ_FP':>7} {'p_FP':>7}")
    for agent, r in sorted(agent_results.items()):
        print(f"{agent:<12} {r['n_a']:>4} {r['n_b']:>4} "
              f"{r['first_pass_acceptance']['A']:>6.3f} {r['first_pass_acceptance']['B']:>6.3f} "
              f"{r['first_pass_acceptance']['delta_B_minus_A']:>+7.3f} {r['first_pass_acceptance']['p']:>7.4f}")
    
    ac_met = {'ac1_sufficient_sample': ac1, 'ac2_significant_difference': ac2, 'ac3_caveats': True}
    print(f"\nAC: {ac_met}")
    if all(ac_met.values()):
        print("[SELF-TEST PASS] All AC met.")
        return 0
    else:
        failed = [k for k,v in ac_met.items() if not v]
        print(f"[AC PARTIAL] Met: {[k for k,v in ac_met.items() if v]}, Failed: {failed}")
        # Even partial results are useful - write them but report honestly
        return 1

if __name__ == '__main__':
    sys.exit(main())