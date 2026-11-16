#!/usr/bin/env python3
"""One-shot: fill missing schema fields in api contract fixture."""
import json, os
fixture_path = os.path.join(os.path.dirname(__file__), "api-fixtures", "contract.json")
d = json.load(open(fixture_path))

schemas = {
    '/api/agents': {'agents': 'list'},
    '/api/file': {'ok': 'bool', 'content': 'str'},
    '/api/file/raw': {'note': 'raw binary response, no JSON'},
    '/api/inference/active-generations': {'generations': 'list', 'count': 'int'},
    '/api/inference/status': {'ok': 'bool', 'status': 'dict'},
    '/api/knowledge-bases': {'bases': 'list'},
    '/api/memory': {'files': 'list', 'count': 'int'},
    '/api/memory/file': {'content': 'str', 'path': 'str'},
    '/api/models': {'models': 'list', 'status': 'dict'},
    '/api/net/dns': {'ok': 'bool', 'result': 'dict'},
    '/api/net/fleet': {'hosts': 'list', 'count': 'int'},
    '/api/net/http': {'ok': 'bool', 'status_code': 'int'},
    '/api/net/latency': {'ok': 'bool', 'ms': 'float'},
    '/api/net/probe': {'ok': 'bool', 'results': 'dict'},
    '/api/rag/knowledge-bases': {'bases': 'list'},
    '/api/rag/search': {'results': 'list', 'count': 'int'},
    '/api/run-state': {'running': 'bool', 'started_at': 'str'},
    '/api/status': {'ok': 'bool', 'version': 'str', 'uptime': 'float'},
    '/api/goals/': {'goals': 'dict', 'agents': 'list'},
}

added = 0
for ep, schema in schemas.items():
    if ep in d and 'schema' not in d[ep]:
        d[ep]['schema'] = schema
        added += 1

d['_meta']['endpoint_count'] = len([k for k in d if k != '_meta'])

with open(fixture_path, 'w') as f:
    json.dump(d, f, indent=2)
print(f'Added {added} schemas. Total endpoints: {d["_meta"]["endpoint_count"]}')