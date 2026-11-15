#!/usr/bin/env python3
"""Extract all API routes from agent_portal.py dispatch logic."""
import re, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
src = open(os.path.join(ROOT, "agent_portal.py"), encoding="utf-8").read()
lines = src.split("\n")

# Find all path dispatch entries: if/elif p == "/api/..."
patterns = re.findall(r'(?:if|elif)\s+p\s*==\s*["\']([^"\']+)["\']', src)
all_routes = sorted(set(patterns))
print(f"Total API routes found: {len(all_routes)}")

# Find do_GET and do_POST method boundaries
got_get_start = got_post_start = None
for i, l in enumerate(lines):
    if 'def do_GET' in l:
        got_get_start = i
    elif 'def do_POST' in l:
        if got_post_start is None:
            got_post_start = i

print(f"do_GET starts at line {got_get_start+1 if got_get_start else '?'}")
print(f"do_POST starts at line {got_post_start+1 if got_post_start else '?'}")

get_routes, post_routes = [], []
for r in all_routes:
    for i, l in enumerate(lines):
        if f'"{r}"' in l or (f"'{r}'" in l):
            if got_get_start and got_post_start:
                if got_get_start <= i < got_post_start:
                    get_routes.append(r)
                else:
                    post_routes.append(r)
            break

print(f"\nGET routes ({len(get_routes)}):")
for r in sorted(get_routes):
    print(f"  GET  {r}")
print(f"\nPOST routes ({len(post_routes)}):")
for r in sorted(post_routes):
    print(f"  POST {r}")
