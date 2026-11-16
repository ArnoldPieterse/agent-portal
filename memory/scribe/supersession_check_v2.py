#!/usr/bin/env python3
"""memory/scribe/supersession_check_v2.py (cycle-2 goal 5, policy owner: Scribe).
v2 fixes over Archivist v1:
  (1) lookbehind (?<![-A-Za-z0-9]) prevents matching SUPERSEDED inside filenames
  (2) is_real_target() filters prose fragments that lack a file extension or known dir prefix
  (3) resolution bug fixed: basename-resolved edges no longer falsely reported as dangling
Exit 0 = PASS (zero cycles, zero dangling), 1 = FAIL.
"""
import os, re, sys, json, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")

SUP = re.compile(r"(?<![-A-Za-z0-9])(supersedes?|replaced by|superseded by)\s*[:\-]?\s*([A-Za-z0-9_./\\-]+)", re.IGNORECASE)

def norm(x):
    x = x.replace("\\", "/")
    while x.startswith("./"): x = x[2:]
    return x

def is_real_target(raw):
    if re.search(r"\.(md|py|json|html)$", raw, re.I):
        return True
    if raw.startswith(("memory/", "ui/", "agents.", "TODO", "MEMORY")):
        return True
    return False

files = set()
for r, d, fs in os.walk(MEM):
    d[:] = [x for x in d if not x.startswith(".")]
    for f in fs: files.add(norm(os.path.relpath(os.path.join(r, f), ROOT)))

bybase = {}
for f in files:
    b2 = f.rsplit("/", 1)[-1]
    bybase.setdefault(b2, f)

edges = []
for rel in sorted(files):
    p = os.path.join(ROOT, *rel.split("/"))
    try: txt = open(p, encoding="utf-8", errors="replace").read()
    except Exception: continue
    for m in SUP.finditer(txt):
        raw = m.group(2)
        if not is_real_target(raw): continue
        edges.append((rel, norm(raw)))

resolved = []
for a, b in edges:
    if b in files or os.path.exists(os.path.join(ROOT, *b.split("/"))):
        resolved.append((a, b, b))
    else:
        rb = bybase.get(b.rsplit("/", 1)[-1])
        resolved.append((a, b, rb if rb else None))

dangling = [(a, b) for a, b, r in resolved if r is None]

adj = collections.defaultdict(set)
for a, b, r in resolved:
    if r: adj[a].add(r)
state, bad = {}, []
def dfs(n):
    state[n] = 1
    for m in adj.get(n, ()):
        if state.get(m) == 1: bad.append((n, m))
        elif not state.get(m): dfs(m)
    state[n] = 2
for n in list(adj):
    if not state.get(n): dfs(n)

report = {
    "run_at": datetime.datetime.now().isoformat(),
    "script": "memory/scribe/supersession_check_v2.py",
    "policy_owner": "Scribe (goal 5)",
    "total_files_scanned": len(files),
    "supersession_markers_found": len(edges),
    "resolved_edges": sum(1 for _,_,r in resolved if r),
    "dangling_heads": len(dangling),
    "cycles_detected": len(bad),
    "dangling_detail": [{"source": a, "target": b} for a, b in dangling],
    "cycle_detail": [{"a": x, "b": y} for x, y in bad],
    "verdict": "PASS" if (not dangling and not bad) else "FAIL"
}

out_path = os.path.join(ROOT, "memory/scribe/supersession-report-v2.json")
with open(out_path, "w") as f:
    json.dump(report, f, indent=2)

print(f"supersession_check v2: {len(edges)} markers, {len(bad)} cycles, {len(dangling)} dangling heads")
for a, b in dangling[:10]:
    print(f"  DANGLING: {a} -> {b}")
print(f"Verdict: {report['verdict']}")
sys.exit(0 if report["verdict"] == "PASS" else 1)
