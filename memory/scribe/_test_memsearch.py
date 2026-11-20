import os, re
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Z:\ (agent_portal.py root)
# Extract the EXACT _memory_search source from agent_portal.py and exec it standalone,
# so we test production code without triggering module-level sandbox discovery.
_src = open(os.path.join(HERE, 'agent_portal.py'), encoding='utf-8').read()
_m = re.search(r"_ROLE_KEYWORDS = \{.*?\n\}\n", _src, re.DOTALL)
_ns = {'re': re, 'HERE': HERE}
exec(_m.group(0), _ns)                                   # defines _ROLE_KEYWORDS
_fn = re.search(r"def _memory_search\(query, top_n=5\):.*?(?=\ndef )", _src, re.DOTALL)
exec(_fn.group(0), _ns)                                  # defines _memory_search
ap = type('A', (), {'_memory_search': staticmethod(_ns['_memory_search'])})

queries = ['hotload', 'winrm reboot recovery', 'contrast tokens css',
           'decision log synthesis', 'cycle narrative', 'compress context briefing',
           'knowledge distillation card', 'fleet health probe', 'mirror revert clobber',
           'goal velocity dashboard', 'anti-stall watchdog wedged', 'memory search ranking']
ok = 0
for q in queries:
    r = ap._memory_search(q)
    res = r['results']
    terms = [t for t in re.split(r'\W+', q.lower()) if len(t) >= 2]
    top_ok = any(any(t in (x['path'] + x['snippet']).lower() for t in terms)
                 or q.lower() in (x['path'] + x['snippet']).lower()
                 for x in res[:1]) if res else False
    ranked = all(res[i]['score'] >= res[i+1]['score'] for i in range(len(res)-1))
    ok += 1 if (res and top_ok and ranked) else 0
    print('  %-28s n=%-3d top=%-46s score=%-6s ranked=%s match=%s'
          % (q, len(res), res[0]['path'] if res else 'NONE',
             res[0]['score'] if res else 0, ranked, top_ok))
print('PASS %d/%d' % (ok, len(queries)))

# exact-match recall: a term that definitely exists must not be a false negative
probe = ap._memory_search('hotload')
assert any('hotload' in x['path'].lower() or 'hotload' in x['snippet'].lower()
           for x in probe['results']), 'false negative on exact term hotload'
print('EXACT-RECALL OK: hotload ->', probe['results'][0]['path'])
