import hashlib, re, json, os, datetime
a = open('agents.json', encoding='utf-8').read()
print('AGENTS md5', hashlib.md5(a.encode()).hexdigest()[:8], '| size', len(a.encode()), '| mtime', datetime.datetime.fromtimestamp(os.path.getmtime('agents.json')).strftime('%H:%M:%S'))
j = json.loads(a)
print('TOP KEYS:', list(j.keys())[:12] if isinstance(j, dict) else type(j))
flat = a
for m in re.finditer(r'"reasoning"\s*:\s*"(\w+)"', flat):
    print('reasoning field ->', m.group(1))
print('count low:', len(re.findall(r'"low"', flat)))
if isinstance(j, dict):
    for k, v in j.items():
        if isinstance(v, dict) and 'reasoning' in v:
            print(k, '=', v['reasoning'])
t = open('TODO.md', encoding='utf-8').read()
print('TODO md5', hashlib.md5(t.encode()).hexdigest()[:8], '| size', len(t.encode()), '| has-R17:', 'R17' in t.upper())
for tok in ('r16b', '4612d8d5', 'arnold-restart-r8'):
    print('TODO contains', tok, ':', tok in t)
agents = j['agents'] if isinstance(j.get('agents'), list) else None
if agents:
    for ag in agents:
        nm = ag.get('name') or ag.get('id') or ag.get('agent')
        print('AGENT', nm, '-> reasoning:', ag.get('reasoning'))
s = open('memory/builder/agent_portal_r16_staged.py', encoding='utf-8').read()
print('STAGED size', len(s.encode()), '| md5-guard refs:', s.count('md5'), '| hashlib import:', 'import hashlib' in s)
st = open('memory/builder/r16_selftest.py', encoding='utf-8').read()
lines = [l for l in st.splitlines() if l.strip()]
print('SELFTEST lines', len(lines), '| tail:', ' | '.join(lines[-3:]))
