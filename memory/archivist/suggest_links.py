#!/usr/bin/env python3
"""archivist/suggest_links.py (cycle-5 goal 3) - Auto-Link Suggestion Engine.
For one KB entry, find the 3 most-related existing entries by a blend of
shared-term TF-IDF cosine similarity and co-citation (entries that point at the
same targets). CLI: python memory/archivist/suggest_links.py --entry <relpath>
[--top 3] [--json]. Exit 0 always; suggestions exclude self-links and duplicates.
"""
import json, math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kb_search as ks
ROOT = ks.ROOT
MEM = os.path.join(ROOT, "memory")
PTR = re.compile(r"->\s*([A-Za-z0-9_./\\-]+\.md)")
MDL = re.compile(r"\[[^\]]*\]\(([^)]+\.md)\)")

def norm(x): return x.replace("\\", "/").lstrip("./")

def _targets(rel):
    """Set of .md files this entry points at (arrows + markdown links)."""
    p = os.path.join(ROOT, rel)
    try: txt = open(p, encoding="utf-8", errors="replace").read()
    except Exception: return set()
    out = set()
    for rx in (PTR, MDL):
        for m in rx.finditer(txt):
            t = norm(m.group(1))
            if os.path.exists(os.path.join(ROOT, t)): out.add(t)
    return out

def _cosine(tf_a, tf_b, idf):
    common = set(tf_a) & set(tf_b)
    if not common: return 0.0
    num = sum((1 + math.log(tf_a[t])) * (1 + math.log(tf_b[t])) * idf.get(t, 1.0) for t in common)
    da = math.sqrt(sum((1 + math.log(v)) ** 2 * idf.get(t, 1.0) for t, v in tf_a.items())) or 1.0
    db = math.sqrt(sum((1 + math.log(v)) ** 2 * idf.get(t, 1.0) for t, v in tf_b.items())) or 1.0
    return num / (da * db)

def suggest(entry_rel, top=3):
    entry_rel = norm(entry_rel)
    c = ks.build_index()
    docs = {d["path"]: d for d in c["docs"]}
    if entry_rel not in docs:
        return {"entry": entry_rel, "error": "not a KB .md leaf", "suggestions": []}
    src_tf, idf = docs[entry_rel]["tf"], c["idf"]
    src_targets = _targets(entry_rel)
    # co-citation: for every OTHER doc, how many of ITS targets the entry also points at
    co = {}
    for other in docs:
        if other == entry_rel: continue
        shared = len(src_targets & _targets(other))
        if shared: co[other] = shared
    mx_co = max(co.values()) if co else 1
    scored = []
    for other, d in docs.items():
        if other == entry_rel: continue
        sim = _cosine(src_tf, d["tf"], idf)
        csc = co.get(other, 0) / mx_co
        score = 0.7 * sim + 0.3 * csc
        if score <= 0: continue
        shared_terms = sorted(set(src_tf) & set(d["tf"]), key=lambda t: -src_tf[t])[:6]
        scored.append({"path": other, "title": d["title"], "score": round(score, 4),
                       "shared_terms": shared_terms,
                       "co_cited_targets": sorted(src_targets & _targets(other))})
    scored.sort(key=lambda x: (-x["score"], x["path"]))
    seen, out = set(), []
    for s in scored:
        if s["path"] in seen or s["path"] == entry_rel: continue
        seen.add(s["path"]); out.append(s)
        if len(out) >= top: break
    return {"entry": entry_rel, "suggestions": out}

if __name__ == "__main__":
    args = sys.argv[1:]
    entry = args[args.index("--entry") + 1] if "--entry" in args else None
    top = int(args[args.index("--top") + 1]) if "--top" in args else 3
    if not entry:
        print("usage: suggest_links.py --entry <relpath> [--top N]"); sys.exit(2)
    r = suggest(entry, top)
    if "--json" in args:
        print(json.dumps(r, indent=1))
    else:
        print("entry:", r["entry"])
        for i, s in enumerate(r["suggestions"], 1):
            print(" %d. %s (%s) score=%.3f terms=%s co_cited=%d"
                  % (i, s["title"], s["path"], s["score"], ",".join(s["shared_terms"][:4]),
                     len(s["co_cited_targets"])))
