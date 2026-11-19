#!/usr/bin/env python3
"""archivist/kb_search.py - TF-IDF search over the memory/ knowledge base.
Shared foundation for goal #9 (/api/kb/search endpoint) and goal #5 (retrieval
benchmark). No external ML libs: pure-Python tokenise + TF-IDF cosine scoring.
Entry = one .md leaf under memory/. Title = first markdown heading, else filename.
CLI: python memory/archivist/kb_search.py "query" [--limit 5] [--json]
"""
import json, math, os, re, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
STOP = set("the a an and or of to in on for with by from is are was were be been being this that these those it its as at not no yes can could will would should may might must do does did done have has had having if then else when while after before during into over under about between across per via via each every any all some such only own same so too very just also both more most less least fewer many much few other another others new old first last next prev previous current recent past future full half part way thing things one two three four five six seven eight nine ten use used using uses usage work works working run runs running make makes made let lets letting take takes taken get gets got go goes went see saw show shows shown set sets setting put puts putting add adds added remove removed delete deleted check checked fix fixed build built create created write written file files dir path code data value values key keys item items entry entries goal goals host hosts agent agents portal panel view page tab button click open opened close closed load loaded save saved sync synced mirror mirrors update updated updated running start started stop stopped test tested verify verified evidence memory index".split())
TOK = re.compile(r"[a-z][a-z0-9_]{2,}")
H1 = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", re.M)
TITLE_BOOST = 3.0  # terms in the entry's own H1 count extra (standard IR title weighting)
_cache = {"ts": 0.0, "docs": [], "idf": {}, "N": 0}

def norm(x): return x.replace("\\", "/").lstrip("./")

def tokenize(t):
    return [w for w in TOK.findall(t.lower()) if w not in STOP]

def _snippet(body, terms, width=220):
    low = body.lower()
    pos = -1
    for t in terms:
        i = low.find(" " + t)
        if i < 0: i = low.find(t)
        if i >= 0 and (pos < 0 or i < pos): pos = i
    if pos < 0: pos = 0
    s = body[max(0, pos - 60): pos + width]
    return ("..." if pos > 60 else "") + re.sub(r"\s+", " ", s).strip() + "..."

def build_index(force=False):
    now = time.time()
    if not force and _cache["docs"] and now - _cache["ts"] < 60: return _cache
    docs, df = [], {}
    for r, d, fs in os.walk(MEM):
        d[:] = [x for x in d if not x.startswith(".")]
        for f in sorted(fs):
            if not f.endswith(".md"): continue
            p = os.path.join(r, f)
            rel = norm(os.path.relpath(p, ROOT))
            try: txt = open(p, encoding="utf-8", errors="replace").read()
            except Exception: continue
            m = H1.search(txt)
            title = m.group(1).strip() if m else f[:-3]
            terms = tokenize(title + " " + txt)
            tf = {}
            for t in terms: tf[t] = tf.get(t, 0) + 1
            ttf = {t for t in tokenize(title)}
            for t in tf: df[t] = df.get(t, 0) + 1
            docs.append({"path": rel, "title": title, "tf": tf, "ttf": ttf,
                         "snippet_head": re.sub(r"\s+", " ", txt[:400]).strip(),
                         "mtime": os.path.getmtime(p)})
    N = len(docs)
    idf = {t: math.log((N + 1) / (c + 1)) + 1.0 for t, c in df.items()}
    _cache.update(ts=now, docs=docs, idf=idf, N=N)
    return _cache

def score_query(q):
    c = build_index()
    qterms = tokenize(q)
    if not qterms: return []
    out = []
    for d in c["docs"]:
        s, hit = 0.0, []
        for t in set(qterms):
            tf = d["tf"].get(t)
            if tf:
                w = (1 + math.log(tf)) * c["idf"].get(t, 1.0)
                if t in d["ttf"]: w *= TITLE_BOOST
                s += w
                hit.append(t)
        if s > 0: out.append((s, hit, d))
    out.sort(key=lambda x: -x[0])
    mx = out[0][0] if out else 1.0
    return [{"path": d["path"], "title": d["title"], "score": round(s / mx, 4),
             "matched_terms": hit[:8],
             "snippet": _snippet(d["snippet_head"] + " " + d["snippet_head"], hit)}
            for s, hit, d in out]

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    limit = 5
    if "--limit" in sys.argv:
        i = sys.argv.index("--limit"); limit = int(sys.argv[i + 1])
    q = " ".join(args)
    res = score_query(q)[:limit]
    if "--json" in sys.argv: print(json.dumps(res, indent=1))
    else:
        for i, r in enumerate(res, 1):
            print("%d. %s  (%s)  [%.3f]" % (i, r["title"], r["path"], r["score"]))
            print("   " + r["snippet"][:180])
