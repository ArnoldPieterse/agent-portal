# Provenance: header added 2026-11-15 by Orchestrator (Archivist goal 6 audit). Original: fleet-ops scripts (Arnold + agent legs); purpose in the docstring/comments below.
"""White: load Q8_0 -> GPU1 alongside quinn-q4 (GPU0). Probe atlas-q8 alias.
Writes white_load_q8_result.json. Run detached; poll the result file."""
import json, time, urllib.request, urllib.error

BASE = 'http://127.0.0.1:8888'
Q8_PATH = r'C:\Users\White\.lmstudio\models\lmstudio-community\Qwen3.8-27B-GGUF'

out = {'steps': []}

def log(step, **kw):
    out['steps'].append({'step': step, 't': time.strftime('%H:%M:%S'), **kw})
    json.dump(out, open('white_load_q8_result.json', 'w'))

def call(method, path, body=None, timeout=1800):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    if data:
        r.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:1200]

def loaded_ids():
    st, b = call('GET', '/api/inference/loaded-models', timeout=60)
    try:
        d = json.loads(b)
        items = d if isinstance(d, list) else d.get('models', d.get('data', []))
        return [m.get('id') or m.get('model_id') for m in items]
    except Exception:
        return ['<unparseable ' + str(b)[:120] + '>']

body = {'model_path': Q8_PATH, 'gguf_variant': 'Q8_0', 'gpu_ids': [1],
        'max_seq_length': 32768, 'cache_type_kv': 'q8_0', 'n_parallel': 1,
        'tensor_parallel': False, 'alongside': True}
ok = False
for attempt in range(12):
    st, resp = call('POST', '/api/inference/load', body)
    log('load_req_a%d' % (attempt + 1), status=st, resp=resp[:500])
    if st in (200, 201):
        break
    if str(st) == '409':
        time.sleep(15)
        continue
    log('verdict', verdict='LOAD_REJECTED')
    raise SystemExit(1)

deadline = time.time() + 2400
while time.time() < deadline:
    time.sleep(20)
    ids = loaded_ids()
    log('poll', loaded=ids)
    if any('Q8_0' in str(i) or 'lmstudio-community' in str(i) for i in ids if i):
        ok = True
        break

def probe(alias, tag):
    payload = json.dumps({'model': alias,
        'messages': [{'role': 'user', 'content': 'Reply with exactly: ' + tag + '-OK'}],
        'max_tokens': 24, 'stream': True}).encode()
    r = urllib.request.Request(BASE + '/v1/chat/completions', data=payload, method='POST')
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

if ok:
    time.sleep(15)
    pa = probe('atlas-q8', 'ATLAS')
    log('probe_atlas', status=pa[0], text=pa[1])
else:
    log('probe_atlas', status='skipped')

st, b = call('GET', '/api/inference/loaded-models', timeout=60)
log('final_loaded_models', status=st, resp=b[:800])
out['verdict'] = 'ALL_UP' if ok else 'PARTIAL'
json.dump(out, open('white_load_q8_result.json', 'w'), indent=1)
print('DONE', out['verdict'])
