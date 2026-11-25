import sys, traceback, json
sys.path.insert(0, 'memory/mechanic')
from winrm_ntlm_full import test_host

hosts = [
    ('PALE',  'IP_PALE', 'pale',  ''),
    ('BLACK', 'IP_BLACK', 'black', ''),
    ('RED',   'IP_LAN', 'red',   ''),
]
results = {}
for name, ip, user, pw in hosts:
    try:
        results[name] = test_host(ip, user, pw)
    except Exception as e:
        tb = traceback.format_exc()
        results[name] = f'{type(e).__name__}: {e}\n{tb}'
print(json.dumps(results, indent=2))
