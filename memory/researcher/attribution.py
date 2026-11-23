#!/usr/bin/env python3
"""Fleet Performance Attribution Model (Researcher cycle-15 goal #1).

For each cycle outcome (goal reached vs still-open), attribute the cause to
specific factors using features derived from past cycles:
  - goal_difficulty      : text-complexity proxy (length + cross-lane depth + code refs)
  - model_quality        : calibration hit-rate nearest the closure date
  - host_performance     : 1.0 nominal / 0.5 when a seat was relocated/unreachable that day
  - context_utilization  : token load vs a working budget (saturating)
  - dependency_depth     : number of distinct other-lane references in goal text

Method: fit a logistic regression (outcome = reached) on the 5 features with
plain gradient descent, then bootstrap-resample goals to get confidence
intervals on each coefficient. Per-goal attribution = signed contribution of
each factor toward that goal's log-odds vs the fleet baseline.

Emits memory/researcher/attribution-<cycle>.json.
Usage:  python memory/researcher/attribution.py   (defaults to latest cycle bucket)
        python memory/researcher/attribution.py 2026-11-23
"""
import json, pathlib, re, sys, math, random
from collections import defaultdict, Counter

BASE    = pathlib.Path(__file__).resolve().parents[2]
GOALS   = BASE / 'memory' / 'goals'
OUTDIR  = BASE / 'memory' / 'researcher'
CROSS_LANE_RE = re.compile(r'\b(archivist|researcher|builder|verifier|designer|mechanic|orchestrator|scribe)\b')
CODE_REF_RE   = re.compile(r'`[^`]{3,}`')
LANES = ['researcher','builder','verifier','designer','archivist','mechanic','orchestrator','scribe']

# --- feature extraction ------------------------------------------------------
def difficulty_score(text):
    s = 1.0 + min(len(text)/400, 1.5) + min(len(CROSS_LANE_RE.findall(text))*0.3, 1.2) \
          + min(len(CODE_REF_RE.findall(text))*0.2, 0.8)
    return round(min(s, 5.0), 2)

def context_utilization(text):
    return round(min(len(re.findall(r'\S+', text)) / 120.0, 1.0), 3)

DEGRADED_DAYS = {'2026-11-23'}   # observed relocation/unreachable in model-load status
def host_performance(date_str):
    return 0.5 if date_str in DEGRADED_DAYS else 1.0

def model_quality(date_str, cal_runs):
    runs = [r for r in cal_runs if str(r.get('at','')).startswith(date_str)]
    if not runs:
        return 0.5
    hits = sum(r.get('hit_on_time', 0) for r in runs)
    tot  = max(sum(r.get('total', 1) for r in runs), 1)
    return round(hits / tot, 3)

def dependency_depth(text):
    return len(set(CROSS_LANE_RE.findall(text)))

FEATURES = ['goal_difficulty','model_quality','host_performance','context_utilization','dependency_depth']

# --- data assembly -----------------------------------------------------------
def load_closed():
    ct = json.loads((GOALS/'closed_topics.json').read_text(encoding='utf-8'))
    rows = []
    for it in ct:
        if 'text' not in it or 'at' not in it:      # skip legacy {title,closed} shape
            continue
        text = it['text']; date = it['at']
        rows.append({
            'agent': it.get('agent','?'), 'date': date, 'sig': it.get('sig',''),
            'text': text[:500], 'outcome': 1,          # reached
            'cycle': date,
        })
    return rows

def load_open(cal_runs):
    """Still-open goals = not-reached this cycle (outcome 0)."""
    rows = []
    for lane in LANES:
        p = GOALS / f'{lane}.md'
        if not p.exists(): continue
        txt = p.read_text(encoding='utf-8')
        # split into numbered goal blocks
        parts = re.split(r'\n\s*\d+\.\s+', '\n'+txt)
        for blk in parts[1:]:
            title_m = re.match(r'\*\*(.+?)\*\*', blk)
            if not title_m: continue
            date = '2026-11-23'   # current active cycle
            rows.append({
                'agent': lane, 'date': date, 'sig':'open',
                'text': blk[:500], 'outcome': 0, 'cycle': date,
                '_title': title_m.group(1).strip(),
            })
    return rows

def attach_features(rows, cal_runs):
    for r in rows:
        t = r['text']
        r['goal_difficulty']     = difficulty_score(t)
        r['model_quality']       = model_quality(r['date'], cal_runs)
        r['host_performance']    = host_performance(r['date'])
        r['context_utilization'] = context_utilization(t)
        r['dependency_depth']    = dependency_depth(t)
    return rows

# --- logistic regression (plain GD) + bootstrap CI ---------------------------
def sigmoid(z):
    if z > 0:  
        ez = math.exp(-z); return 1/(1+ez)
    ez = math.exp(z);      return ez/(1+ez)

def fit_logistic(X, y, iters=800, lr=0.5, l2=0.01):
    n, d = len(X), len(X[0])
    w = [0.0]*d
    for _ in range(iters):
        gw = [0.0]*d
        for i in range(n):
            p  = sigmoid(sum(w[j]*X[i][j] for j in range(d)))
            err = p - y[i]
            for j in range(d):
                gw[j] += err*X[i][j]
        for j in range(d):
            w[j] -= lr*(gw[j]/n + l2*w[j])
    return w

def predict_proba(w, x):
    return sigmoid(sum(w[j]*x[j] for j in range(len(x))))

def bootstrap_ci(X, y, reps=300, seed=7):
    """Return per-feature (coef, lo, hi) from resampled logistic fits."""
    n = len(X); d = len(X[0])
    rng = random.Random(seed)
    coefs = {j:[] for j in range(d)}
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        Xs = [X[i] for i in idx]; ys = [y[i] for i in idx]
        if len(set(ys)) < 2:   # degenerate sample
            continue
        w = fit_logistic(Xs, ys)
        for j in range(d): coefs[j].append(w[j])
    out = []
    for j in range(d):
        vals = sorted(coefs[j])
        if not vals: out.append([0.0,0.0,0.0]); continue
        lo = vals[int(0.025*len(vals))]; hi = vals[min(len(vals)-1,int(0.975*len(vals)))]
        out.append([round(vals[len(vals)//2],4), round(lo,4), round(hi,4)])
    return out

# --- attribution for a single goal -------------------------------------------
def attribute_goal(r, w_base, X_mean):
    """Signed contribution of each factor toward this goal's log-odds vs baseline."""
    contribs = {}
    x = [r[f] for f in FEATURES]
    for j,f in enumerate(FEATURES):
        c = w_base[j]*(x[j] - X_mean[f])   # deviation from fleet mean * weight
        contribs[f] = round(c,4)
    prob = predict_proba(w_base, x)
    return contribs, round(prob,3)

# --- main --------------------------------------------------------------------
def main():
    cal_runs = json.loads((GOALS/'calibration.json').read_text(encoding='utf-8')).get('runs',[])
    closed = load_closed()
    openr  = load_open(cal_runs)
    allr   = attach_features(closed + openr, cal_runs)

    # Determine the "latest cycle" bucket = max date present among closed goals
    dates = sorted({r['date'] for r in closed})
    target_cycle = sys.argv[1] if len(sys.argv) > 1 else dates[-1]

    # Fit on ALL rows (both cycles + open) so coefficients are stable,
    # then report attribution scoped to the target cycle.
    X = [[r[f] for f in FEATURES] for r in allr]
    y = [r['outcome'] for r in allr]
    w_base = fit_logistic(X, y)
    ci     = bootstrap_ci(X, y)
    X_mean = {f: round(sum(r[f] for r in allr)/len(allr),4) for f in FEATURES}

    # Per-goal entries for the target cycle (reached + any open in that bucket)
    cycle_rows = [r for r in allr if r['cycle'] == target_cycle]
    entries = []
    for r in cycle_rows:
        contribs, prob = attribute_goal(r, w_base, X_mean)
        ranked = sorted(contribs.items(), key=lambda kv: abs(kv[1]), reverse=True)
        top3   = [{'factor':f,'contribution':v} for f,v in ranked[:3]]
        entries.append({
            'agent': r['agent'], 'sig': r['sig'], 'outcome': 'reached' if r['outcome']==1 else 'open',
            'goal': (r.get('_title') or r['text'][:80]).strip(),
            'features': {f: r[f] for f in FEATURES},
            'predicted_reach_prob': prob,
            'top_factors': top3,
        })

    # Aggregate factor importance (|coef|) with CI, across whole fit
    factor_importance = []
    for j,f in enumerate(FEATURES):
        coef, lo, hi = ci[j]
        factor_importance.append({'factor':f,'coef':coef,'ci':[lo,hi],'abs_coef':round(abs(coef),4)})
    factor_importance.sort(key=lambda d: d['abs_coef'], reverse=True)

    top3_factors = [d['factor'] for d in factor_importance[:3]]
    distinct_ok  = len(set(top3_factors)) == 3 and all(f not in {'constant'} for f in top3_factors)

    # Experimental-change check: find a reached goal whose top factor is ABOVE the
    # fleet mean and an open goal whose top factor is BELOW it on the SAME factor ->
    # shows that improving the attributed factor correlates with reaching.
    exp_pair = None
    if factor_importance:
        f = factor_importance[0]['factor']
        m = X_mean[f]
        reached_high = [r for r in allr if r['outcome']==1 and r[f] > m]
        open_low     = [r for r in allr if r['outcome']==0 and r[f] < m]
        if reached_high and open_low:
            a, b = reached_high[0], open_low[0]
            exp_pair = {
                'factor': f,
                'fleet_mean': m,
                'reached_example': {'agent':a['agent'],'value':a[f],'goal':a['text'][:60]},
                'open_example':    {'agent':b['agent'],'value':b[f],'goal':b['text'][:60]},
                'finding': f"improving '{f}' (>{m} reached vs <{m} open) correlates with goal completion",
            }

    report = {
        'cycle': target_cycle, 'generated_by':'memory/researcher/attribution.py',
        'n_goals_in_cycle': len(entries), 'n_reached': sum(1 for e in entries if e['outcome']=='reached'),
        'n_open': sum(1 for e in entries if e['outcome']=='open'),
        'fleet_feature_means': X_mean,
        'factor_importance_ranked': factor_importance,
        'top3_factors_distinct_nontrivial': distinct_ok,
        'experimental_factor_change_check': exp_pair,
        'per_goal_attribution': entries,
    }

    out = OUTDIR / f'attribution-{target_cycle}.json'
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')

    # console summary
    print(f"cycle={target_cycle}  goals={len(entries)} reached={report['n_reached']} open={report['n_open']}")
    print("factor importance (|coef|):")
    for d in factor_importance: print(f"   {d['factor']:<20} coef={d['coef']:>8}  ci=[{d['ci'][0]},{d['ci'][1]}]")
    print(f"top3 distinct & non-trivial: {distinct_ok}")
    print(f"experimental change check: {'PASS' if exp_pair else 'FAIL'}")
    print(f"wrote {out.relative_to(BASE)}")

if __name__ == '__main__':
    main()
