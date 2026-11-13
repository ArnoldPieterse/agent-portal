"""Detached post-verdict chain for Red (launch AFTER this turn ends).
1) wait for the final verdict in red_setup_result2.json (waiter \\RedQ8Wait2 writes it; max 4h)
2) on DUAL_UP: red_smoke.py -> idle-wait -> smoke8.py -> idle-wait -> group_e2e.py (serial subprocesses;
   full streams, no early aborts - smoke6 lesson)
3) summary in red_chain_result.json; non-DUAL_UP verdicts recorded as STOPPED_<verdict>.
"""
import json, time, urllib.request, subprocess, sys

LOG = []
def P(s):
    LOG.append("[%s] %s" % (time.strftime("%H:%M:%S"), s))
    print(s, flush=True)

PORTAL = "http://127.0.0.1:8099"
HEALTH = "http://127.0.0.1:8888/api/health"

def save(summary):
    summary['log'] = LOG
    json.dump(summary, open('red_chain_result.json', 'w', encoding='utf-8'), indent=1)

def wait_idle(maxs=600):
    deadline = time.time() + maxs
    while time.time() < deadline:
        try:
            d = json.load(urllib.request.urlopen(HEALTH, timeout=10))
            if not d.get('inference_active'):
                P('studio idle')
                return True
        except Exception as e:
            P('health err: %s' % str(e)[:120])
        time.sleep(15)
    return False

def run_script(name, logname):
    t0 = time.time()
    with open(logname, 'w', encoding='utf-8') as lf:
        p = subprocess.run([sys.executable, name], stdout=lf, stderr=subprocess.STDOUT,
                           timeout=6*3600)
    P('%s exit=%d %.0fs' % (name, p.returncode, time.time()-t0))
    return p.returncode

def readj(path):
    try:
        return json.load(open(path, encoding='utf-8'))
    except Exception as e:
        return {'_read_err': str(e)[:200]}

# ---- 1) wait for the Red verdict ----
verdict = None
deadline = time.time() + 4*3600
while time.time() < deadline:
    try:
        res = json.load(open('red_setup_result2.json', encoding='utf-8'))
        if res.get('verdict'):
            verdict = res['verdict']
            break
    except Exception:
        pass
    time.sleep(60)

summary = {'started': time.strftime('%H:%M:%S'), 'red_verdict': verdict}
if not verdict:
    summary['chain_verdict'] = 'STOPPED_TIMEOUT_WAITING_VERDICT'
    save(summary); P('DONE STOPPED_TIMEOUT_WAITING_VERDICT'); sys.exit(0)

if verdict != 'DUAL_UP':
    res = readj('red_setup_result2.json')
    summary['chain_verdict'] = 'STOPPED_' + verdict
    summary['steps_tail'] = res.get('steps', [])[-8:]
    summary['copy_tail'] = res.get('copy_tail', '')
    save(summary); P('DONE STOPPED_' + verdict); sys.exit(0)

# ---- 2) DUAL_UP chain ----
P('red DUAL_UP -> red_smoke (Red-only, no local slot contention)')
run_script('red_smoke.py', 'red_chain_redsmoke.log')
summary['red_smoke'] = readj('red_smoke_result.json')

if not wait_idle():
    summary['chain_verdict'] = 'ABORT_STILL_BUSY_BEFORE_SMOKE8'
    save(summary); P('DONE ABORT'); sys.exit(0)
run_script('smoke8.py', 'red_chain_smoke8.log')
summary['smoke8'] = readj('smoke8_result.json')

if not wait_idle():
    summary['chain_verdict'] = 'ABORT_STILL_BUSY_BEFORE_GROUP'
    save(summary); P('DONE ABORT'); sys.exit(0)
run_script('group_e2e.py', 'red_chain_group.log')
summary['group_e2e'] = readj('group_e2e_result_8agent.json')

rs = summary.get('red_smoke', {}).get('verdict', '?')
s8 = summary.get('smoke8', {}).get('verdict', '?')
ge = summary.get('group_e2e', {})
summary['chain_verdict'] = ('CHAIN_OK' if (rs == 'ALL_OK' and s8 == 'ALL_OK' and ge.get('concluded'))
                            else 'CHAIN_PARTIAL')
summary['finished'] = time.strftime('%H:%M:%S')
save(summary)
P('DONE', summary['chain_verdict'])