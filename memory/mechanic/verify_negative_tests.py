"""Negative + positive tests for perf_profile.verify() — runs in sandbox, no :8099 needed."""
import sys, json, pathlib, tempfile
sys.path.insert(0, 'memory/mechanic')
import perf_profile
from perf_profile import verify

def run_case(label, metrics):
    tmp = pathlib.Path(tempfile.mktemp(suffix='.json'))
    tmp.write_text(json.dumps({'metrics': metrics}))
    orig = perf_profile.OUT_PATH
    perf_profile.OUT_PATH = str(tmp)
    try:
        r = verify()
    finally:
        perf_profile.OUT_PATH = orig
        tmp.unlink(missing_ok=True)
    return r

# Case 1: all null (sandbox-blocked output) -> must FAIL
r1 = run_case('null percentiles', {
    k: {'status':'no_samples','p50':None,'p95':None,'p99':None}
    for k in ['portal_health','fleet_status','goals_api','llm_models']
})
print(f'null percentiles       -> {"FAIL (correct)" if not r1 else "PASS (BUG!)"}')

# Case 2: p50 > p95 (out of order) -> must FAIL
r2 = run_case('out-of-order', {
    'portal_health': {'status':'ok','p50':95.0,'p95':50.0,'p99':99.0},
    'fleet_status':  {'status':'ok','p50':10.0,'p95':20.0,'p99':30.0},
    'goals_api':     {'status':'ok','p50':5.0, 'p95':10.0,'p99':15.0},
    'llm_models':    {'status':'ok','p50':50.0,'p95':80.0,'p99':95.0}
})
print(f'out-of-order p50>p95   -> {"FAIL (correct)" if not r2 else "PASS (BUG!)"}')

# Case 3: all good -> must PASS
r3 = run_case('good data', {
    'portal_health': {'status':'ok','p50':12.3,'p95':45.6,'p99':78.9},
    'fleet_status':  {'status':'ok','p50':8.1, 'p95':22.4,'p99':55.0},
    'goals_api':     {'status':'ok','p50':5.2, 'p95':15.7,'p99':30.1},
    'llm_models':    {'status':'ok','p50':50.0,'p95':120.0,'p99':200.0}
})
print(f'good data              -> {"PASS (correct)" if r3 else "FAIL (BUG!)"}')

all_ok = (not r1) and (not r2) and r3
print(f'\nRESULT: {"ALL CORRECT" if all_ok else "BUG DETECTED"}'  )
import datetime
with open('memory/mechanic/verify-negative-tests-2026-11-20.jsonl','a') as f:
    f.write(json.dumps({'ts':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'null_rejected':not r1,'out_of_order_rejected':not r2,
                        'good_accepted':r3,'all_correct':all_ok}) + '\n')
print('Evidence: memory/mechanic/verify-negative-tests-2026-11-20.jsonl')
