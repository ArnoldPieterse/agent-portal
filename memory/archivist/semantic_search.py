#!/usr/bin/env python3
"""archivist/semantic_search.py - TF-IDF semantic search over memory/ leaves.

Goal: lightweight relevance ranking over all memory/**/*.md knowledge leaves,
ranked by cosine similarity of TF-IDF vectors (not just keyword match). A small
curated fleet-domain synonym table is applied to BOTH query and docs so that
synonymous phrasings match (e.g. "host down" finds a leaf saying "machine
unreachable").

Usage:
  python memory/archivist/semantic_search.py --query "<text>" [--top N] [--rebuild]

Exit codes: 0 = ok, 1 = fatal.
No external deps (stdlib only). Index cached to semantic-index.json; --rebuild forces rebuild.
"""
import os, re, sys, json, math, time, argparse
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # repo root (memory/..)
MEM  = os.path.join(ROOT, "memory")
CACHE = os.path.join(HERE, "semantic-index.json")

# --- fleet-domain synonym groups: first member is the canonical form ---------
SYNONYM_GROUPS = [
    ["host", "machine", "node", "server", "box"],
    ["down", "unreachable", "offline", "dead", "lost", "unavailable", "died"],
    ["model", "llm", "weights"],
    ["vram", "gpu"],
    ["error", "failure", "failed", "fault", "broken", "failures"],
    ["fix", "repair", "remediation", "resolved", "patch", "fixed"],
    ["agent", "bot", "seat", "worker"],
    ["alert", "incident", "warning", "anomaly"],
    ["load", "reload", "swap", "switch", "loaded"],
    ["oom", "outofmemory", "memorypressure"],
]
_CANON = {}
for _g in SYNONYM_GROUPS:
    for _t in _g:
        _CANON[_t] = _g[0]

STOP = set("a an the and or of to in on for with is are was were be been being it its this that these those at by from as not no yes if then else when while do does did can could should would may might will shall we you they i he she our your their his her my me us them so such than too very just also only more most less least per via without within into onto upon about against between among during before after above below up out over under again further once here there what which who whom why how all any both each few other same some s t d ll m o re ve ain aren couldn didn doesn hadn hasn haven isn ma mightn mustn needn shan shouldn wasn weren won wouldn".split())

TOK = re.compile(r"[a-z0-9_]+")

def norm(tok):
    return _CANON.get(tok, tok)

def tokenize(text):
    out = []
    for w in TOK.findall(text.lower()):
        if len(w) < 2 or w in STOP or w.isdigit():
            continue
        c = norm(w)
        if c in STOP:
            continue
        out.append(c)
    return out

def build_index(verbose=False):
    t0 = time.time()
    docs = []
    df = Counter()
    for dirpath, _dirs, files in os.walk(MEM):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
            except Exception:
                continue
            toks = tokenize(text)
            if not toks:
                continue
            tf = Counter(toks)
            for t in tf:
                df[t] += 1
            docs.append({"path": rel, "tf": tf, "len": len(toks)})
    n = max(1, len(docs))
    idf = {t: math.log((n + 1) / (d + 1)) + 1.0 for t, d in df.items()}
    # precompute weighted vectors + norms
    for d in docs:
        vec = {}
        norm2 = 0.0
        for t, f in d["tf"].items():
            w = (1.0 + math.log(f)) * idf[t]
            vec[t] = w
            norm2 += w * w
        d["vec"] = vec
        d["norm"] = math.sqrt(norm2) if norm2 else 1.0
    idx = {"n_docs": n, "idf_keys": len(idf), "docs": docs}
    with open(CACHE, "w", encoding="utf-8") as fh:
        json.dump(idx, fh)
    dt = time.time() - t0
    if verbose:
        print(f"[index] {n} docs, {len(idf)} terms, rebuilt in {dt:.2f}s -> {os.path.relpath(CACHE, ROOT)}")
    return idx, dt

def load_index(force=False):
    if not force and os.path.exists(CACHE):
        with open(CACHE, "r", encoding="utf-8") as fh:
            return json.load(fh), 0.0
    return build_index(verbose=True)

def query(idx, text, top=5):
    qtoks = tokenize(text)
    if not qtoks:
        return []
    # idf reconstructed from stored norms is unavailable; recompute df-free weight via doc freq proxy:
    # use the cached per-doc vec values as the weighting basis (they already embed idf).
    # For the query, weight each token by mean of its value across docs that contain it.
    qweight = {}
    for t in set(qtoks):
        vals = [d["vec"][t] for d in idx["docs"] if t in d["vec"]]
        qweight[t] = (sum(vals) / len(vals)) if vals else 0.0
    qnorm = math.sqrt(sum(w * w for w in qweight.values())) or 1.0
    scored = []
    for d in idx["docs"]:
        dot = sum(qweight[t] * d["vec"][t] for t in qweight if t in d["vec"])
        if dot <= 0:
            continue
        sim = dot / (qnorm * d["norm"])
        scored.append((sim, d["path"]))
    scored.sort(key=lambda x: -x[0])
    return scored[:top]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    if not a.query:
        ap.error("--query is required")
    idx, dt = load_index(force=a.rebuild)
    res = query(idx, a.query, a.top)
    print(f"# query: {a.query!r}  ({idx['n_docs']} docs)  index={dt:.2f}s")
    if not res:
        print("(no matches)")
    for i, (sim, path) in enumerate(res, 1):
        print(f"{i}. {sim:.4f}  {path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())