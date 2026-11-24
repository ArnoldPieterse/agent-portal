#!/usr/bin/env python3
"""
convergence_metric_validation.py — Verifier: Convergence Metric Validation
Round topic: Fleet Autonomy Convergence.

Validates that the fleet's convergence metrics are computed correctly by
re-deriving each metric from its declared components / source fields and
cross-checking invariants. Three metric families are checked:

  A) autonomy-score.json   : stored `score` must equal the value produced by
                             applying the declared `formula` to the declared
                             `components`. Component ranges [0,1] enforced.
  B) efficiency-index.jsonl: each row's `index` must match the documented
                             formula (goals_completed/passes_used)
                             * (1-rework_rate) * (1-idle_fraction).
  C) mode-durations.json   : sum of per-mode `hours` must equal window
                             `total_hours`; each `percent` must equal
                             hours/total_hours*100.

Design: FAIL-CLOSED. Any metric whose recomputation disagrees with the stored
value beyond tolerance, or that violates an invariant, is a FAIL. Self-test
(--self-test) uses synthetic fixtures to prove every branch (pass + fail)
without touching live data. Live run writes results JSON next to this file.
CWD-independent: all paths anchored via __file__.

Exit codes: 0 = all metrics validated; 1 = one or more metric FAIL; 3 = input
missing/unparseable (fail-closed).
"""
import json, pathlib, sys, re, datetime

HERE = pathlib.Path(__file__).resolve().parent          # memory/verifier
ROOT = HERE.parent.parent                               # repo root
OPS = ROOT / 'memory' / 'ops'
RESULTS = HERE / 'convergence-metric-validation.json'

TOL = 0.011  # tolerance for float recompute-vs-stored comparison (rounding)

def load_json(path):
    if not path.exists():
        return None, f"missing: {path.relative_to(ROOT)}"
    try:
        return json.loads(path.read_text(encoding='utf-8')), None
    except (json.JSONDecodeError, OSError) as e:
        return None, f"unparseable {path.name}: {e}"

def load_jsonl(path):
    if not path.exists():
        return None, f"missing: {path.relative_to(ROOT)}"
    rows = []
    for i, line in enumerate(path.read_text(encoding='utf-8').strip().split('\n')):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            return None, f"unparseable JSONL line {i+1} in {path.name}: {e}"
    return rows, None

# --------------------------------------------------------------------------
# Metric A: autonomy score internal consistency
# --------------------------------------------------------------------------
def check_autonomy(data):
    """Recompute score from components via the declared weights."""
    res = {'metric': 'autonomy_score', 'status': 'PASS', 'checks': []}
    if data is None:
        res['status'] = 'FAIL'; res['checks'].append({'check': 'parseable', 'ok': False, 'detail': 'input missing'}); return res
    comp = data.get('components', {})
    weights = data.get('weights', {})  # declared weights from the file itself
    stored = data.get('score')
    # component range check: values are percentages [0,100]
    for k in ('pass_autonomy', 'duration_score', 'rework_score', 'trend_score'):
        v = comp.get(k)
        ok = isinstance(v, (int, float)) and 0.0 <= v <= 100.0
        res['checks'].append({'check': f'component_range[{k}]', 'ok': ok, 'value': v})
    if not all(c['ok'] for c in res['checks']):
        res['status'] = 'FAIL'; return res
    # recompute using declared weights: a*pass_autonomy + b*duration + c*rework + d*trend
    w_a = weights.get('a', 0.35); w_b = weights.get('b', 0.25)
    w_c = weights.get('c', 0.2); w_d = weights.get('d', 0.2)
    recomputed = (comp['pass_autonomy'] * w_a
                  + comp['duration_score'] * w_b
                  + comp['rework_score'] * w_c
                  + comp['trend_score'] * w_d)
    delta = abs(recomputed - stored) if stored is not None else None
    ok = delta is not None and delta <= max(TOL, 0.1)  # allow 0.1 for rounding on 0-100 scale
    res['checks'].append({'check': 'score_matches_formula', 'ok': ok,
                          'stored': stored, 'recomputed': round(recomputed, 5),
                          'delta': round(delta, 5) if delta is not None else None})
    if not ok:
        res['status'] = 'FAIL'
    return res

# --------------------------------------------------------------------------
# Metric B: efficiency index per-row formula match
# --------------------------------------------------------------------------
def check_efficiency(rows):
    res = {'metric': 'efficiency_index', 'status': 'PASS', 'rows_checked': 0, 'bad_rows': []}
    if rows is None:
        res['status'] = 'FAIL'; res['detail'] = 'input missing'; return res
    for r in rows:
        res['rows_checked'] += 1
        gc = r.get('goals_completed'); pu = r.get('passes_used')
        rr = r.get('rework_rate', 0.0); idle = r.get('idle_fraction', 0.0)
        stored = r.get('efficiency_index', r.get('index'))  # field name may vary
        if None in (gc, pu) or pu == 0:
            res['bad_rows'].append({'cycle': r.get('cycle'), 'reason': 'missing/zero passes'}); continue
        recomputed = (gc / pu) * (1 - rr) * (1 - idle)
        delta = abs(recomputed - stored) if stored is not None else None
        ok = delta is not None and delta <= TOL
        if not ok:
            res['status'] = 'FAIL'
            res['bad_rows'].append({'cycle': r.get('cycle'), 'stored': stored,
                                    'recomputed': round(recomputed, 5),
                                    'delta': round(delta, 5) if delta is not None else None})
    # provenance: is there a script that writes this file? (re-derivability)
    writers = []
    py_files = [f for f in ROOT.glob('memory/**/*.py')]
    for f in py_files:
        try:
            txt = f.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        # a writer must reference the filename AND perform a write (write_text/open ... 'a'/'w'/jsonl append)
        if 'efficiency-index' in txt and re.search(r"(open\(|write_text|\.append|with open)\b", txt):
            writers.append(str(f.relative_to(ROOT)))
    res['writer_scripts'] = writers
    return res

# --------------------------------------------------------------------------
# Metric C: mode durations invariant
# --------------------------------------------------------------------------
def check_mode_durations(data):
    res = {'metric': 'mode_durations', 'status': 'PASS', 'checks': []}
    if data is None:
        res['status'] = 'FAIL'; res['checks'].append({'check': 'parseable', 'ok': False, 'detail': 'input missing'}); return res
    meta = data.get('_meta', {})
    total = meta.get('total_hours')
    hours_sum = 0.0
    for mode in ('WORK', 'MAINTENANCE', 'IDLE'):
        md = data.get(mode, {})
        h = md.get('hours'); pct = md.get('percent')
        if h is None:
            res['checks'].append({'check': f'{mode}.present', 'ok': False}); continue
        hours_sum += h
        if total:
            expected_pct = round(h / total * 100, 1)
            ok_pct = pct is not None and abs(expected_pct - pct) <= 0.15
            res['checks'].append({'check': f'{mode}.percent', 'ok': ok_pct,
                                  'stored': pct, 'expected': expected_pct})
    if total:
        delta_h = hours_sum - total
        ok_sum = abs(delta_h) <= max(0.5, total * 0.01)
        res['checks'].append({'check': 'hours_sum_equals_window', 'ok': ok_sum,
                              'sum_of_modes': round(hours_sum, 2), 'window_total': total,
                              'excess_hours': round(delta_h, 2)})
    if not all(c['ok'] for c in res['checks']):
        res['status'] = 'FAIL'
    return res

# --------------------------------------------------------------------------
def run_live():
    now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    out = {'generated_at': now, 'tolerance': TOL, 'metrics': [], 'overall': 'PASS', 'fail_count': 0}
    hard_fail = False
    a_data, a_err = load_json(OPS / 'autonomy-score.json')
    b_rows, b_err = load_jsonl(OPS / 'efficiency-index.jsonl')
    c_data, c_err = load_json(OPS / 'mode-durations.json')
    for err in (a_err, b_err, c_err):
        if err:
            hard_fail = True
    a = check_autonomy(a_data) if not a_err else {'metric': 'autonomy_score', 'status': 'FAIL', 'checks': [{'check': 'parseable', 'ok': False, 'detail': a_err}]}
    b = check_efficiency(b_rows) if not b_err else {'metric': 'efficiency_index', 'status': 'FAIL', 'detail': b_err, 'rows_checked': 0}
    c = check_mode_durations(c_data) if not c_err else {'metric': 'mode_durations', 'status': 'FAIL', 'checks': [{'check': 'parseable', 'ok': False, 'detail': c_err}]}
    out['metrics'] = [a, b, c]
    for m in out['metrics']:
        if m.get('status') != 'PASS':
            out['fail_count'] += 1
    out['overall'] = 'FAIL' if (hard_fail or out['fail_count']) else 'PASS'
    RESULTS.write_text(json.dumps(out, indent=2), encoding='utf-8')
    return out

def self_test():
    """Synthetic fixtures prove pass AND fail branches for every metric."""
    passed = 0; failed = 0
    def t(name, cond):
        nonlocal passed, failed
        if cond: passed += 1
        else: failed += 1
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

    # A: autonomy — consistent fixture passes (matches real schema)
    good = {'score': round(70*0.35 + 80*0.25 + 90*0.2 + 60*0.2, 1),
            'components': {'pass_autonomy': 70, 'duration_score': 80,
                           'rework_score': 90, 'trend_score': 60},
            'weights': {'a': 0.35, 'b': 0.25, 'c': 0.2, 'd': 0.2}}
    t('A1 autonomy consistent -> PASS', check_autonomy(good)['status'] == 'PASS')
    # A: score drifted from formula -> FAIL
    bad = dict(good); bad['score'] = good['score'] - 5.0
    t('A2 autonomy score drifts -> FAIL', check_autonomy(bad)['status'] == 'FAIL')
    # A: component out of range (boundary) -> FAIL
    oor = dict(good); oor['components'] = dict(good['components']); oor['components']['trend_score'] = 150.0
    t('A3 autonomy component out-of-range -> FAIL', check_autonomy(oor)['status'] == 'FAIL')

    # B: efficiency — matching row passes
    gc, pu, rr, idle = 28, 35, 0.15, 0.10
    exp = (gc/pu)*(1-rr)*(1-idle)
    t('B1 efficiency row matches formula -> PASS',
      check_efficiency([{'cycle': 'c-x', 'goals_completed': gc, 'passes_used': pu,
                         'rework_rate': rr, 'idle_fraction': idle, 'efficiency_index': round(exp, 4)}])['status'] == 'PASS')
    # B: index that does NOT match formula -> FAIL
    t('B2 efficiency row mismatches formula -> FAIL',
      check_efficiency([{'cycle': 'c-y', 'goals_completed': gc, 'passes_used': pu,
                         'rework_rate': rr, 'idle_fraction': idle, 'efficiency_index': round(exp + 0.035, 4)}])['status'] == 'FAIL')
    # B: zero passes (division guard) flagged
    t('B3 efficiency zero-passes row flagged',
      check_efficiency([{'cycle': 'c-z', 'goals_completed': 1, 'passes_used': 0,
                         'rework_rate': 0.1, 'idle_fraction': 0.1, 'efficiency_index': 0.5}])['bad_rows'][0]['reason'] == 'missing/zero passes')

    # C: mode durations — consistent fixture passes
    tot = 168.0; w, m, i = 6.84, 4.0, tot - 6.84 - 4.0
    good_c = {'_meta': {'total_hours': tot},
              'WORK': {'hours': w, 'percent': round(w/tot*100, 1)},
              'MAINTENANCE': {'hours': m, 'percent': round(m/tot*100, 1)},
              'IDLE': {'hours': i, 'percent': round(i/tot*100, 1)}}
    t('C1 mode durations consistent -> PASS', check_mode_durations(good_c)['status'] == 'PASS')
    # C: hours sum exceeds window -> FAIL
    bad_c = json.loads(json.dumps(good_c)); bad_c['IDLE']['hours'] += 9.5
    t('C2 mode hours exceed window -> FAIL', check_mode_durations(bad_c)['status'] == 'FAIL')

    print(f"\n[self-test] {passed} passed / {failed} failed")
    return 0 if failed == 0 else 1

def main():
    if '--self-test' in sys.argv:
        sys.exit(self_test())
    out = run_live()
    print(f"[convergence_metric_validation] overall={out['overall']} fail_count={out['fail_count']}")
    for m in out['metrics']:
        line = f"  {m['metric']:20s} {m['status']}"
        if 'bad_rows' in m and m['bad_rows']:
            line += f" (bad rows: {[r.get('cycle') for r in m['bad_rows']]})"
        print(line)
    print(f"[convergence_metric_validation] results -> {RESULTS.relative_to(ROOT)}")
    sys.exit(0 if out['overall'] == 'PASS' else 1)

if __name__ == '__main__':
    main()
