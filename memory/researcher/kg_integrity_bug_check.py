#!/usr/bin/env python3
"""Repro/verify for kg_integrity.py `to` vs `target` supersession-endpoint bug.
Reads memory/archivist/knowledge_graph.json and prints current(buggy) vs fixed metrics + path/junk split.
No writes to Archivist's files. Run: python memory/researcher/kg_integrity_bug_check.py
"""
import json, os
from collections import defaultdict

kg = json.load(open("memory/archivist/knowledge_graph.json"))
edges = kg.get("edges", [])
sup   = kg.get("supersessions", [])

def compute(use_fixed):
    nodes=set(); inbound=defaultdict(int); dangling=[]
    for e in edges:
        nodes.add(e["from"]); nodes.add(e["to"]); inbound[e["to"]]+=1
        if not os.path.exists(e["to"]): dangling.append(e["to"])
    for s in sup:
        frm=s.get("from","")
        tgt=(s.get("target") if use_fixed else s.get("to","")) or ""
        nodes.add(frm); nodes.add(tgt); inbound[tgt]+=1
        if tgt and not os.path.exists(tgt): dangling.append(tgt)
    nodes={n for n in nodes if n}
    orphans=[n for n in nodes if inbound[n]==0]
    return dict(nodes=len(nodes), orphan_count=len(orphans), dangling_ref=len(dangling))

cur=compute(False); fix=compute(True)
print(f"{'metric':18} {'current(buggy)':>16} {'naive-fix':>12}")
for k in ("nodes","orphan_count","dangling_ref"):
    print(f"{k:18} {cur[k]:>16} {fix[k]:>12}")
paths=sum(1 for s in sup if isinstance(s.get("target"),str) and "/" in s["target"])
junk =len(sup)-paths
print(f"\nsupersessions total={len(sup)}  path-like targets={paths}  junk-token targets={junk}")
print("VERDICT: orphan count unaffected by bug; dangling_ref=0 is a false negative (targets never checked).")
print("        naive to->target fix over-counts dangling (327/343 targets are non-path junk) -> filter to path-like.")
