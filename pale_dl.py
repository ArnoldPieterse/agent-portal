import urllib.request, urllib.error, json
H = {'Authorization': 'Bearer sk-unsloth-f3c04f0ea9784dd512534cafdb5efc34', 'Content-Type': 'application/json'}
B = 'http://IP_PALE:8888'
for repo, var in [('unsloth/Qwen3.8-27B-GGUF', 'UD-Q4_K_XL'), ('lmstudio-community/Qwen3.8-27B-GGUF', 'Q8_0')]:
    try:
        r = urllib.request.urlopen(urllib.request.Request(B + '/api/hub/download', data=json.dumps({'repo_id': repo, 'gguf_variant': var}).encode(), method='POST', headers=H), timeout=30)
        print(repo, var, r.status, r.read().decode()[:120])
    except urllib.error.HTTPError as e:
        print(repo, var, 'ERR', e.code, e.read().decode()[:150])
