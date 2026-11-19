#!/usr/bin/env python3
"""archivist/weekly_digest.py (cycle-5 goal 10).
Weekly digest: new entries, updated entries, orphan changes (knowledge graph),
retrieval quality delta vs last run. Writes memory/archivist/digest-WW-YYYY.md.
Exit 0 always."""
import json, os, re, subprocess, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GIT = os.path.join(ROOT, "mingit", "cmd", "git.exe") if os.path.exists(
    os.path.join(ROOT, "mingit", "cmd", "git.exe")) else "git"
MEM = "memory"

def git(*args):
    try:
        out = subprocess.run([GIT] + list(args), cwd=ROOT, capture_output=True,
                             text=True, timeout=60)
        return [l for l in out.stdout.splitlines() if l.strip()]
    except Exception:
        return []

def md_files(lines):
    seen, out = set(), []
    for l in lines:
        m = re.match(r"memory/.*\.md$", l.strip())
        if m and l not in seen:
            seen.add(l); out.append(l)
    return sorted(out)

def kg_stats():
    """Fresh knowledge graph stats incl. orphan count (in-degree 0)."""
    try:
        subprocess.run([sys.executable, "memory/archivist/knowledge_graph.py"],
                       cwd=ROOT, capture_output=True, timeout=120)
        g = json.load(open(os.path.join(HERE, "knowledge_graph.json"), encoding="utf-8"))
        indeg = {}
        for e in g.get("edges", []):
            indeg[e["to"]] = indeg.get(e["to"], 0) + 1
        nodes = set()
        for e in g.get("edges", []):
            nodes.add(e["from"]); nodes.add(e["to"])
        orphans = sorted(n for n in nodes if indeg.get(n, 0) == 0)
        return {"node_count": g.get("node_count"), "edge_count": g.get("edge_count"),
                "orphan_count": len(orphans), "orphans": orphans}
    except Exception as ex:
        return {"error": str(ex)}

def retrieval_stats():
    p = os.path.join(HERE, "retrieval_metrics.json")
    if not os.path.exists(p):
        return None
    try:
        m = json.load(open(p, encoding="utf-8"))
        return {k: m[k] for k in ("precision_at_5", "recall_at_10", "mrr") if k in m}
    except Exception:
        return None

def main():
    now = datetime.now()
    iso = now.isocalendar()
    tag = "digest-%02d-%04d.md" % (iso[1], iso[0])
    out = os.path.join(HERE, tag)

    new_f = md_files(git("log", "--since=7 days ago", "--name-only",
                         "--diff-filter=A", "--", "memory"))
    mod_f = md_files(git("log", "--since=7 days ago", "--name-only",
                         "--diff-filter=M", "--", "memory"))

    kg = kg_stats()
    snap_p = os.path.join(HERE, "digest-kg-snapshot.json")
    prev_kg = None
    if os.path.exists(snap_p):
        try:
            prev_kg = json.load(open(snap_p, encoding="utf-8"))
        except Exception:
            prev_kg = None
    json.dump(kg, open(snap_p, "w", encoding="utf-8"), indent=1)

    ret = retrieval_stats()
    prev_ret = None
    prev_p = os.path.join(HERE, "retrieval_metrics_prev.json")
    if os.path.exists(prev_p):
        try:
            pm = json.load(open(prev_p, encoding="utf-8"))
            prev_ret = {k: pm[k] for k in ("precision_at_5", "recall_at_10", "mrr") if k in pm}
        except Exception:
            prev_ret = None

    L = ["# Weekly digest - %s (week %d of %d)" % (now.strftime("%Y-%m-%d"), iso[1], iso[0]), "",
         "## 1. New entries added (git, last 7 days)", ""]
    if new_f:
        L += ["- %s" % f for f in new_f]
    else:
        L.append("- none")
    L += ["", "## 2. Entries updated (git, last 7 days)", ""]
    if mod_f:
        L += ["- %s" % f for f in mod_f[:40]]
        if len(mod_f) > 40: L.append("- ... and %d more" % (len(mod_f) - 40))
    else:
        L.append("- none")
    L += ["", "## 3. Orphan changes (knowledge graph)", ""]
    if "error" in kg:
        L.append("- graph build failed: %s" % kg["error"])
    else:
        L.append("- current: %s nodes, %s edges, %s orphans (in-degree 0)"
                 % (kg.get("node_count"), kg.get("edge_count"), kg.get("orphan_count")))
        if prev_kg and "error" not in prev_kg:
            d = {k: (kg.get(k) or 0) - (prev_kg.get(k) or 0) for k in
                 ("node_count", "edge_count", "orphan_count")}
            L.append("- delta vs previous digest run: nodes %+d, edges %+d, orphans %+d"
                     % (d["node_count"], d["edge_count"], d["orphan_count"]))
        else:
            L.append("- delta: baseline recorded (no previous snapshot)")
    L += ["", "## 4. Retrieval quality delta", ""]
    if ret:
        L.append("- current: P@5=%s R@10=%s MRR=%s" % (ret.get("precision_at_5"),
                    ret.get("recall_at_10"), ret.get("mrr")))
        if prev_ret:
            for k in ("precision_at_5", "recall_at_10", "mrr"):
                a, b = prev_ret.get(k), ret.get(k)
                if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    L.append("- %s: %s -> %s (%+d)" % (k, a, b, 100 * (b - a)))
        else:
            L.append("- delta: baseline recorded (no previous metrics)")
    else:
        L.append("- no retrieval_metrics.json found (run retrieval_benchmark.py first)")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("weekly_digest: %s (new=%d updated=%d)" % (os.path.relpath(out, ROOT), len(new_f), len(mod_f)))

if __name__ == "__main__":
    main()
