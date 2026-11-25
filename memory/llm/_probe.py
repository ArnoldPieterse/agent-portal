t = open("agent_portal.py", encoding="utf-8").read().splitlines()
for i, l in enumerate(t):
    s = l.strip()
    if s.startswith(("import ", "from ")) and ("portal" in s or "handler" in s or "gpu" in s):
        print(i + 1, s[:80])
print("---")
for i, l in enumerate(t):
    if 'elif p == "/api/models":' in l or 're.match(r"^/api/agents' in l:
        print(i + 1, l.strip()[:60])