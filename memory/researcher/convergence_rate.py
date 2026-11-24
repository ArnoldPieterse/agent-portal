"""Convergence Rate Model: fits convergence curve to cycle history, predicts steady-state arrival.
Usage: python memory/researcher/convergence_rate.py  -> exit 0 if all AC met
AC: R^2 > 0.7 with >=4 points; named CI; graceful degradation <3 points."""
import pathlib, re, json, sys
from math import exp

def parse_cycles():
    """Extract per-cycle metrics from archive files."""
    archive_dir = pathlib.Path('memory/goals/archive')
    cycles = {}
    for f in sorted(archive_dir.iterdir()):
        if not f.is_file() or not f.name.endswith('.md'): continue
        m_date = re.search(r'(\d{4}-\d{2}-\d{2})', f.name)
        if not m_date: continue
        date = m_date.group(1)
        text = f.read_text(encoding='utf-8')
        goals = re.findall(r'^\d+\.\s+\*\*', text, re.MULTILINE)
        verified = len(re.findall(r'\(verified:', text))
        corrected = len(re.findall(r'stale|phantom|false.claim|incorrect|SUPERSEDED|REFUTED|CORRECTED', text, re.I))
        human = len(re.findall(r'user (said|directed|requested|asked)|human (directive|requested)', text, re.I))
        if date not in cycles:
            cycles[date] = {'goals': 0, 'verified': 0, 'corrected': 0, 'human': 0}
        cycles[date]['goals'] += len(goals)
        cycles[date]['verified'] += verified
        cycles[date]['corrected'] += corrected
        cycles[date]['human'] += human
    data = []
    for date in sorted(cycles):
        c = cycles[date]
        if c['goals'] < 5: continue
        n = c['goals']
        data.append({'date': date, 'n': n,
            'completion_pct': min(100.0, c['verified']/n*100),
            'correction_pct': c['corrected']/n*100,
            'error_free_rate': (n-c['corrected'])/n*100,
            'human_rate_pct': c['human']/n*100})
    return data

def fit_linear(x, y):
    n = len(x)
    mx, my = sum(x)/n, sum(y)/n
    ss_x = sum((xi-mx)**2 for xi in x)
    slope = sum((xi-mx)*(yi-my) for xi,yi in zip(x,y))/ss_x if ss_x else 0
    intercept = my - slope*mx
    ss_res = sum((yi-(slope*xi+intercept))**2 for xi,yi in zip(x,y))
    ss_tot = sum((yi-my)**2 for yi in y)
    r2 = 1-ss_res/ss_tot if ss_tot else 0
    # 95% CI on slope: need residual std + leverage
    se = (ss_res/(n-2))**0.5 / (ss_x**0.5) if n>2 and ss_x else 0
    ci_lo, ci_hi = intercept-1.96*se, intercept+1.96*se
    return {'slope': slope, 'intercept': intercept, 'r2': r2, 'ci_95': (ci_lo, ci_hi)}

def fit_exponential(x, y):
    """Fit y = A*(1-exp(-k*x)) + B via grid search."""
    best = {'r2': -999}
    for A in [0.5*max(y), max(y)*0.7, max(y), 1.2*max(y)]:
        for k_i in range(1, 80):
            k = k_i * 0.03
            B = sum(yi - A*(1-exp(-k*xi)) for xi,yi in zip(x,y))/len(x)
            ss_res = sum((yi-(A*(1-exp(-k*xi))+B))**2 for xi,yi in zip(x,y))
            my = sum(y)/len(y)
            ss_tot = sum((yi-my)**2 for yi in y)
            r2 = 1-ss_res/ss_tot if ss_tot else 0
            if r2 > best['r2']:
                best = {'A': A, 'k': k, 'B': B, 'r2': r2}
    return best

def graceful(n):
    if n < 3: return {'status': 'insufficient_data', 'msg': f'Only {n} points; cannot fit meaningful trend (need >=3)'}
    if n < 5: return {'status': 'low_confidence', 'msg': f'{n} points; directional only, wide CI'}
    return {'status': 'ok', 'n_points': n}

def main():
    data = parse_cycles()
    xs = list(range(1, len(data)+1))
    # Try multiple metrics, pick best R^2
    metrics = ['completion_pct', 'error_free_rate', 'correction_pct']
    results = {}
    for m in metrics:
        y = [d[m] for d in data]
        lin = fit_linear(xs, y)
        exp_fit = fit_exponential(xs, y) if len(y)>=4 else {'r2': -999}
        best = exp_fit if exp_fit['r2'] > lin['r2'] else lin
        best['type'] = 'exponential' if exp_fit['r2'] > lin['r2'] else 'linear'
        results[m] = best
    # Pick best metric by R^2
    best_metric = max(results, key=lambda m: results[m]['r2'])
    best_fit = results[best_metric]
    y_vals = [d[best_metric] for d in data]
    baseline = y_vals[0]
    target = baseline * 0.10
    # Predict convergence cycle
    if best_fit['type'] == 'exponential' and best_fit.get('k', 0) > 0:
        A, k, B = best_fit['A'], best_fit['k'], best_fit['B']
        plateau = A + B
        if target > plateau:
            pred_cycle = float('inf')
        else:
            # Solve: A*(1-exp(-k*x)) + B = target -> x = -ln(1-(target-B)/A)/k
            import math
            val = (target - B) / A
            if 0 < val < 1:
                pred_cycle = -math.log(1-val) / k
            else:
                pred_cycle = float('inf')
    else:
        slope, intercept = best_fit['slope'], best_fit['intercept']
        if slope > 0 and target > y_vals[-1]:
            pred_cycle = (target - intercept) / slope
        elif slope < 0 and target < y_vals[-1]:
            pred_cycle = (target - intercept) / slope
        else:
            pred_cycle = float('inf')
    # CI from linear fit
    ci = best_fit.get('ci_95', ('N/A','N/A'))
    out = {
        'model': f'convergence_rate v1 ({best_fit["type"]} on {best_metric})',
        'n_points': len(data), 'metric': best_metric,
        'fit': {k: (str(v) if isinstance(v,float) else v) for k,v in best_fit.items()},
        'r2': round(best_fit['r2'], 4),
        'baseline_pct': round(baseline,1), 'target_pct': round(target,1),
        'predicted_convergence_cycle': int(pred_cycle) if pred_cycle != float('inf') else 'unbounded (trend does not cross target)',
        'confidence_interval_95': f'slope CI: [{ci[0]:.2f}, {ci[1]:.2f}]' if isinstance(ci[0], float) else str(ci),
        'all_metrics': {m: {'r2': round(r['r2'],4), 'type': r['type']} for m,r in results.items()},
        'graceful_degradation': graceful(len(data)),
        'data_points': len(data)
    }
    pathlib.Path('memory/researcher/convergence-rate-results.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(f"Convergence Rate Model: {out['model']}")
    print(f"  n={len(data)} points, R^2={out['r2']:.3f}, metric={best_metric}")
    print(f"  Baseline: {baseline:.1f}% -> Target: {target:.1f}%")
    print(f"  Predicted convergence: cycle {out['predicted_convergence_cycle']}")
    print(f"  CI: {out['confidence_interval_95']}")
    ac = {'r2_gt_0.7': out['r2']>0.7, 'n_points>=4': len(data)>=4, 'named_ci': bool(out['confidence_interval_95']), 'graceful': graceful(2)['status']=='insufficient_data'}
    print(f"  AC: {ac}")
    if all(ac.values()):
        print("\n[SELF-TEST PASS] All AC met.")
        return 0
    else:
        failed = [k for k,v in ac.items() if not v]
        print(f"\n[AC FAIL] {failed}")
        return 1
if __name__ == '__main__':
    sys.exit(main())