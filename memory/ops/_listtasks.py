import csv
rows = list(csv.DictReader(open(r'C:\Projects\Workspace\memory\ops\_tasks.csv', encoding='utf-8', errors='ignore')))
for r in rows:
    n = (r.get('TaskName') or '').strip()
    keep = any(k in n for k in ('AgentPortal', 'Fleet', 'LlamaRPC', 'Mirror', 'Portal', 'RecoverAll', 'Verify', 'WinRM'))
    if keep:
        print(n, '|', (r.get('Status') or '')[:12], '=>', (r.get('Task To Run') or '')[:130])
