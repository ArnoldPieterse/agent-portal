#!/usr/bin/env python3
"""archivist/supersession_check.py (cycle-2 goal 5, script owner per charter).
Finds every supersession marker ("supersedes"/"replaced by"/"superseded by") across memory/,
builds the chain graph and validates: (a) acyclic, (b) every chain terminates at a canonical
head that still exists. Exit 0 = valid, 1 = cycle or dangling head."""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
SUP = re.compile(r"(?i)\b(supersedes?|replaced by|superseded by)\s*[:\-]?\s*([A-Za-z0-9_./\\-]+)")

def norm(x): return x.replace("\\", "/").lstrip("./")

files = set()
for r, d, fs in os.walk(MEM):
    d[:] = [x for x in d if not x.startswith(".")]
    for f in fs: files.add(norm(os.path.relpath(os.path.join(r, f), ROOT)))

edges = []   # (older -> newer) : "X supersedes Y" means X is newer head
for rel in files:
    p = os.path.join(ROOT, *rel.split("/"))
    try: txt = open(p, encoding="utf-8", errors="replace").read()
    except Exception: continue
    for m in SUP.finditer(txt):
        raw = m.group(2)
        # prose filter: a real target looks like a path (has / or an extension), else it's English
        if "/" not in raw and not re.search(r"\.(md|py|json|html)$", raw, re.I):
            continue
        tgt = norm(raw)
        edges.append((rel, tgt))

# cycle detection (DFS) on newer->older direction
import collections
adj = collections.defaultdict(set)
for a, b in edges: adj[a].add(b)
state, bad = {}, []
def dfs(n):
    state[n] = 1
    for m in adj.get(n, ()):
        if state.get(m) == 1: bad.append((n, m))
        elif not state.get(m): dfs(m)
    state[n] = 2
for n in list(adj): 
    if not state.get(n): dfs(n)

dangling = [(a, b) for a, b in edges if b not in files and not os.path.exists(os.path.join(ROOT, *b.split("/")))]
print("supersession_check: %d markers, %d cycles, %d dangling heads" % (len(edges), len(bad), len(dangling)))
for a, b in bad[:5]: print("  CYCLE: %s <-> %s" % (a, b))
for a, b in dangling[:5]: print("  DANGLING head: %s -> %s" % (a, b))
sys.exit(1 if (bad or dangling) else 0)
