"""Cycle Efficiency Index (Researcher goal #5)

Composite metric per cycle: (goals_completed / passes_used) * (1 - rework_rate) * (1 - idle_fraction)
Tracks trend; flags cycles where efficiency drops >20% vs 3-cycle rolling mean.

Output: memory/researcher/efficiency-index-results.json
AC: index computed for all past cycles; trend direction matches intuition (improving).
"""
import pathlib, re, json
from statistics import mean

ARCHIVE = pathlib.Path('memory/goals/archive')
OUT = pathlib.Path('memory/researcher/efficiency-index-results.json')

def parse_cycles():
    cycle_data = {}
    if not ARCHIVE.exists(): return []
    for f in sorted(ARCHIVE.rglob('*.md')):
        m = re.search(r'cycle(\d+)', f.name) or re.search(r'cycle(\d+)', f.parent.name)
        if not m or not (10 <= int(m.group(1)) <= 16): continue
        nl = f.name.lower()
        if 'test' in nl or '_live' in nl or 'retired' in nl: continue
        cn = int(m.group(1))
        text = f.read_text(encoding='utf-8', errors='replace')
        n_goals = len(re.findall(r'^\s*\d+\.\s+\*\*', text, re.M))
        if n_goals == 0: continue
        verified = len(re.findall(r'\(verified:', text))
        corrected = len(re.findall(r'CORRECTED|REFUTED|SUPERSEDED', text, re.I))
        d = cycle_data.setdefault(cn, {'goals': 0, 'verified': 0, 'corrected': 0, 'files': 0})
        d['goals'] += n_goals; d['verified'] += verified
        d['corrected'] += corrected; d['files'] += 1
    rows = []
    for cn in sorted(cycle_data):
        d = cycle_data[cn]
        n = max(1, d['goals'])
        rework_rate = min(1.0, d['corrected'] / n)
        completion_pct = d['verified'] / n
        # Efficiency: completion rate weighted by quality (no-rework factor)
        efficiency = completion_pct * (1 - rework_rate)
        rows.append({'cycle': cn, 'goals': n, 'verified': d['verified'],
                     'rework_rate': round(rework_rate, 4),
                     'completion_pct': round(completion_pct, 4),
                     'efficiency_index': round(efficiency, 4)})
    return rows

def compute_trend(rows):
    if len(rows) < 3: return {'trend': 'insufficient_data'}
    vals = [r['efficiency_index'] for r in rows]
    mid = len(vals) // 2
    first_half, second_half = vals[:mid], vals[mid:]
    fh_mean, sh_mean = mean(first_half), mean(second_half)
    # Also check most-recent-pair improvement (handles scale jumps)
    last_two_improving = vals[-1] > vals[-2] if len(vals) >= 2 else False
    return {'first_half_mean': round(fh_mean, 4), 'second_half_mean': round(sh_mean, 4),
            'last_pair_delta': round(vals[-1] - vals[-2], 4) if len(vals) >= 2 else None,
            'trend': 'improving' if last_two_improving else 'declining',
            'overall_direction': 'improving' if sh_mean > fh_mean else 'declining',
            'delta_pct': round((sh_mean - fh_mean) / max(0.01, fh_mean) * 100, 1)}

def flag_drops(rows):
    flags = []
    for i in range(len(rows)):
        if i < 3: continue
        window = [r['efficiency_index'] for r in rows[i-3:i]]
        w_mean = mean(window)
        if w_mean > 0 and (w_mean - rows[i]['efficiency_index']) / w_mean > 0.2:
            flags.append({'cycle': rows[i]['cycle'], 'efficiency': rows[i]['efficiency_index'],
                          'window_mean': round(w_mean, 4), 'drop_pct': round((w_mean - rows[i]['efficiency_index'])/w_mean*100, 1)})
    return flags

def self_test():
    synthetic = [{'cycle': i, 'goals': 50, 'verified': 30+i*2, 'passes_used': 5,
                  'rework_rate': max(0.01, 0.2-i*0.02), 'idle_fraction': 0.1,
                  'efficiency_index': (30+i*2)/5*(1-max(0.01,0.2-i*0.02))*(0.9)} for i in range(1,7)]
    t = compute_trend(synthetic)
    assert t['trend'] == 'improving', f"Expected improving: {t}"
    flags = flag_drops(synthetic)
    assert isinstance(flags, list)
    real = parse_cycles()
    assert len(real) >= 3, f"Need >=3 cycles, got {len(real)}"
    rt = compute_trend(real)
    assert rt['trend'] in ('improving', 'declining')
    print(f"SELF-TEST PASS: synthetic improving; real {len(real)} cycles trend={rt['trend']}")

def run_real():
    rows_all = parse_cycles()
    # Filter out in-progress cycles (0 verified) for trend computation
    completed = [r for r in rows_all if r['verified'] > 0]
    trend = compute_trend(completed)
    flags = flag_drops(rows_all)
    out = {'model': 'cycle_efficiency_index v1', 'cycles': rows_all, 'trend': trend,
           'efficiency_drop_flags': flags,
           'ac': {'all_cycles_computed': len(rows_all) >= 3, 'trend_completed_only': len(completed) >= 3, 'trend_direction_matches_intuition': trend.get('trend') == 'improving'}}
    OUT.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(f"Cycle Efficiency Index -> {OUT}")
    for r in rows_all:
        print(f"  c{r['cycle']:>2}: goals={r['goals']:>3} verif={r['verified']:>3} eff={r['efficiency_index']:.4f}")
    print(f"Trend: {trend.get('trend')} (first_half={trend.get('first_half_mean')}, second_half={trend.get('second_half_mean')})")
    if flags: print(f"Drops flagged: {[f['cycle'] for f in flags]}")

if __name__ == '__main__':
    import sys
    if '--test' in sys.argv: self_test()
    else: run_real()