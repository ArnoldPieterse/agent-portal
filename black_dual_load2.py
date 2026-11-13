"""Black dual-load v2: UD-Q4_K_S -> GPU0, Q8_0 -> GPU1.
Aliases builder-q8 / verifier-q4 (role-named agents). Writes black_dual_load_result.json.
Run detached; poll the result file."""
import json, time, urllib.request, urllib.error
import host_api

KEY = host_api.load_key('BLACK')
BASE = 'http://192.168.1.99:8888'
Q8_REF = 'ref:bc7ad351c9c8d9397ecfdbd0e0afd3e7'
Q8_PATH = r'C:\Users\black\models\Qwen3.8-27B-Q8_0'
S_PATH = r'C:\Users\black\models\Qwen3.8-27B-Q4_K_S'
S_ID = 'Qwen3.8-27B-UD-Q4_K_S'   # folder-scanned id (real file, verified header+size)

out = {'steps': []}

def log(step, **kw):
    out['steps'].append({'step': step, 't': time.strftime('%H:%M:%S'), **kw})
    json.dump(out, open('black_dual_load_result.json', 'w'))

def call(method, path, body=None, timeout=1800):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header('Authorization', 'Bearer ' + KEY)
    if data:
        r.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:1200]

# 1. multi-model fit mode (mirror White: enabled+fit; send ONLY 'mode' per build quirk)
st, body = call('PUT', '/api/settings/multi-model', {'mode': 'fit'})
log('multi_model', status=st, resp=body[:300])

def loaded_ids():
    st, b = call('GET', '/api/inference/loaded-models', timeout=60)
    try:
        d = json.loads(b)
        items = d if isinstance(d, list) else d.get('models', d.get('data', []))
        return [m.get('id') or m.get('model_id') for m in items]
    except Exception:
        return ['<unparseable ' + str(b)[:120] + '>']

def load(label, model_path, variant, gpu, ctx, alongside=False):
    body = {'model_path': model_path, 'gguf_variant': variant, 'gpu_ids': [gpu],
            'max_seq_length': ctx, 'cache_type_kv': 'q8_0', 'n_parallel': 1,
            'tensor_parallel': False}
    if alongside:
        body['alongside'] = True
    for attempt in range(12):
        st, resp = call('POST', '/api/inference/load', body)
        log(label + '_load_req_a%d' % (attempt + 1), status=st, resp=resp[:500])
        if st in (200, 201):
            break
        if str(st) == '409':
            time.sleep(15)
            continue
        return False
    # poll until it shows loaded
    deadline = time.time() + 2400
    while time.time() < deadline:
        time.sleep(20)
        ids = loaded_ids()
        log(label + '_poll', loaded=ids)
        if any(model_path.split('\\')[-1] in str(i) or variant in str(i) or S_ID in str(i) for i in ids if i):
            return True
    return False

ok_s = load('S_q4k', S_PATH, 'UD-Q4_K_S', 0, 65536)
ok_q8 = load('Q8', Q8_PATH, 'Q8_0', 1, 32768, alongside=True)

# aliases: role-named (agents Builder/Verifier). PUT replaces the whole list.
st, body = call('PUT', '/api/settings/model-aliases', {'aliases': [
    {'name': 'builder-q8', 'model': Q8_REF},
    {'name': 'verifier-q4', 'model': S_ID}]})
log('aliases', status=st, resp=body[:300])

def probe(alias, tag):
    payload = json.dumps({'model': alias,
        'messages': [{'role': 'user', 'content': 'Reply with exactly: ' + tag + '-OK'}],
        'max_tokens': 24, 'stream': True}).encode()
    r = urllib.request.Request(BASE + '/v1/chat/completions', data=payload, method='POST')
    r.add_header('Authorization', 'Bearer ' + KEY)
    r.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(r, timeout=300) as resp:
            got = []
            for line in resp:
                t = line.decode().strip()
                if t.startswith('data:') and '[DONE]' not in t:
                    try:
                        d = json.loads(t[5:].strip())
                        got.append(d['choices'][0]['delta'].get('content') or '')
                    except Exception:
                        pass
            return 200, ''.join(got)[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]

time.sleep(15)
pf = probe('builder-q8', 'BUILDER')
log('probe_builder', status=pf[0], text=pf[1])
pv = probe('verifier-q4', 'VERIFIER')
log('probe_verifier', status=pv[0], text=pv[1])

st, body = call('GET', '/api/inference/loaded-models', timeout=60)
log('final_loaded_models', status=st, resp=body[:800])
out['verdict'] = 'ALL_UP' if (ok_s and ok_q8 and pf[0] == 200 and pv[0] == 200) else 'PARTIAL'
json.dump(out, open('black_dual_load_result.json', 'w'), indent=1)
print('DONE', out['verdict'])
