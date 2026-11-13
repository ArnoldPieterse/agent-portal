import json, re, sys, urllib.request, urllib.error

def load_key(host):
    if host == 'RED':
        # Arnold, chat 2026-11-11. Supersedes the stale key left in RED_RPC_ROOTCAUSE.md (401 on it).
        return 'sk-unsloth-a8b6573db2959db2ea4358293938532f'
    if host == 'BLACK':
        # Arnold, chat 2026-11-11 ~14:00. REFRESHED key (old one 401s). Chat-only; mirrors the Red pattern.
        return 'sk-unsloth-31292e7ecc83e8a6e7bd52e59276d307'
    raise ValueError(host)

def base_for(host):
    if host == 'RED':
        return 'http://192.168.1.245:8888'
    return json.load(open('tunnel_urls.json'))['BLACK']

def _jwt_black():
    import os
    pw = os.environ.get('RA_PASSWORD') or '131991Apiet'
    r = urllib.request.Request(base_for('BLACK') + '/api/auth/login',
        data=json.dumps({'username': 'unsloth', 'password': pw}).encode(), method='POST')
    r.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read().decode())['access_token']

def call(host, method, path, body=None, timeout=120):
    key = load_key('RED') if host == 'RED' else _jwt_black()
    url = base_for(host) + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header('Authorization', 'Bearer ' + key)
    if data:
        r.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode()[:800]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:800]

if __name__ == '__main__':
    host, method, path = sys.argv[1], sys.argv[2].upper(), sys.argv[3]
    body = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
    print(call(host, method, path, body))
