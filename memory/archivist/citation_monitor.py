#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""citation_monitor.py - Archivist Goal (cycle-10): verify every pointer citation
in the goal files resolves to a real file that is indexed in its agent INDEX.md.

Usage:
  python citation_monitor.py            # report to stdout + memory/archivist/citation-report.json
"""
import json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GOALS = os.path.join(ROOT, "memory", "goals")
POINTER_RE = re.compile(r"\(\s*pointer:\s*([A-Za-z0-9_./\\-]+)\s*\)")

AGENTS = ["archivist", "builder", "designer", "mechanic", "orchestrator",
          "researcher", "scribe", "verifier"]

def check():
    results, dangling, indexed_missing = [], 0, 0
    for agent in AGENTS:
        gp = os.path.join(GOALS, agent + ".md")
        if not os.path.exists(gp):
            continue
        text = open(gp, encoding="utf-8", errors="replace").read()
        idx_path = os.path.join(ROOT, "memory", agent, "INDEX.md")
        idx_text = open(idx_path, encoding="utf-8", errors="replace").read() if os.path.exists(idx_path) else ""
        for m in POINTER_RE.finditer(text):
            target = m.group(1).replace("\\", "/")
            exists = os.path.exists(os.path.join(ROOT, target))
            indexed = (target in idx_text) or (os.path.basename(target) in idx_text)
            if not exists:
                dangling += 1
            elif not indexed:
                indexed_missing += 1
            results.append({"agent": agent, "pointer": target,
                            "exists": exists, "indexed": indexed})
    total = len(results)
    ok = total - dangling - indexed_missing
    return {"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "total_pointers": total,
            "resolved_and_indexed": ok, "dangling": dangling,
            "unindexed": indexed_missing,
            "health": "OK" if (dangling == 0 and indexed_missing == 0) else "ATTENTION",
            "details": results}

def main():
    r = check()
    out = os.path.join(HERE, "citation-report.json")
    json.dump(r, open(out, "w", encoding="utf-8"), indent=1)
    print(f"pointers={r['total_pointers']} ok={r['resolved_and_indexed']} "
          f"dangling={r['dangling']} unindexed={r['unindexed']} -> {r['health']}")
    for d in r["details"]:
        if not (d["exists"] and d["indexed"]):
            print(f"  [{agent_flag(d)}] {d['pointer']} exists={d['exists']} indexed={d['indexed']}")

def agent_flag(d):
    return "MISSING" if not d["exists"] else "UNINDEXED"

if __name__ == "__main__":
    main()
