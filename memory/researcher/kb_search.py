"""KB SEARCH (2026-11-18) -- queryable confidence-annotated knowledge base (Goal #3).

Searches memory/researcher/dictionary_*.json and returns matching terms WITH the
confidence annotations: {term, definition, usage, confidence, sources, last_verified}.
This is the drop-in logic for the portal /api/kb/search endpoint (Builder wires it).

Run:
  python memory/researcher/kb_search.py <query> [--limit N] [--json]
  python memory/researcher/kb_search.py --selftest

Never raises on bad input; returns [] on no matches.
"""
import json
import os
import re
import argparse

_HERE = os.path.dirname(os.path.abspath(__file__))
DICT_FILES = [os.path.join(_HERE, "dictionary_core.json"),
              os.path.join(_HERE, "dictionary_project.json")]

_STOP = set("a an the and or but of in on at by with from to for is are was were be do does did have has had will would can could should may might not no yes i you he she it we they this that these those there what which who how why all any both each more most other some such only own same so than too very just also now please tell show give add fix complete continue reboot agent task goal loop module reply record".split())

_cache = {"sig": None, "entries": []}


def _stem(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 5 and w.endswith("ing"):
        return w[:-3]
    if len(w) > 4 and w.endswith("ed"):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _tokens(s):
    return [t for t in re.findall(r"[a-z0-9]+", (s or "").lower()) if t not in _STOP]


def load_entries(refresh=False):
    """Load annotated entries -> list of dicts (all fields incl. confidence/sources/last_verified)."""
    try:
        sig = tuple((f, os.path.getmtime(f)) for f in DICT_FILES if os.path.exists(f))
        if not refresh and _cache["sig"] == sig:
            return _cache["entries"]
        entries = []
        for f in DICT_FILES:
            if not os.path.exists(f):
                continue
            raw = json.load(open(f, encoding="utf-8"))
            for k, v in raw.items():
                if k.startswith("_"):
                    continue
                if isinstance(v, dict):
                    e = {"term": k,
                         "definition": str(v.get("definition", "")),
                         "usage": str(v.get("usage", "")),
                         "confidence": float(v.get("confidence", 0.0)),
                         "sources": list(v.get("sources", [])),
                         "last_verified": str(v.get("last_verified", ""))}
                elif isinstance(v, (list, tuple)) and v:
                    e = {"term": k,
                         "definition": str(v[0]),
                         "usage": str(v[1]) if len(v) > 1 else "",
                         "confidence": None, "sources": [], "last_verified": ""}
                else:
                    continue
                entries.append(e)
        _cache["sig"] = sig
        _cache["entries"] = entries
        return entries
    except Exception:
        return []


def score(entry, q_tokens):
    term = entry["term"].lower()
    term_stems = {_stem(w) for w in re.findall(r"[a-z0-9]+", term)} | {term}
    body = (entry["definition"] + " " + entry["usage"]).lower()
    s = 0.0
    for q in q_tokens:
        qs = _stem(q)
        if term == q or term == qs:
            s += 5.0
        elif q in term_stems or qs in term_stems or (q in term and len(q) >= 3):
            s += 2.0
        elif qs in body or (q in body and len(q) >= 4):
            s += 1.0
    return s


def search(query, limit=10):
    """Return ranked list of annotated entries matching query."""
    try:
        q_tokens = _tokens(query)
        if not q_tokens:
            return []
        entries = load_entries()
        scored = [(score(e, q_tokens), e) for e in entries]
        scored = [(s, e) for s, e in scored if s > 0]
        # tie-break: higher confidence first, then term
        scored.sort(key=lambda x: (-x[0], -(x[1]["confidence"] or 0), x[1]["term"]))
        return [dict(e, _score=s) for s, e in scored[:max(0, int(limit))]]
    except Exception:
        return []


def selftest():
    """Prove the acceptance behavior: a search returns confidence + sources + last_verified."""
    entries = load_entries(refresh=True)
    annotated = [e for e in entries if e["confidence"] is not None and e["last_verified"]]
    total = len(entries)
    # pick a known term to query
    sample_term = None
    for e in entries:
        if e["term"]: 
            sample_term = e["term"]
            break
    results = search(sample_term, limit=3) if sample_term else []
    ok_fields = bool(results) and all(
        ("confidence" in r and "sources" in r and "last_verified" in r) for r in results)
    report = {
        "total_entries": total,
        "annotated_entries": len(annotated),
        "pct_annotated": round(100.0 * len(annotated) / total, 1) if total else 0.0,
        "sample_query": sample_term,
        "sample_result_fields_ok": ok_fields,
        "sample_result": results[0] if results else None,
    }
    passed = (len(annotated) == total and total > 0 and ok_fields)
    report["PASS"] = passed
    return report


def main():
    ap = argparse.ArgumentParser(description="Search confidence-annotated KB")
    ap.add_argument("query", nargs="?", help="search query")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--json", action="store_true", help="output JSON")
    ap.add_argument("--selftest", action="store_true", help="run acceptance self-test")
    a = ap.parse_args()
    if a.selftest:
        rep = selftest()
        print(json.dumps(rep, indent=2))
        raise SystemExit(0 if rep["PASS"] else 1)
    if not a.query:
        print("usage: kb_search.py <query> [--limit N] [--json] | --selftest")
        raise SystemExit(2)
    res = search(a.query, limit=a.limit)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        if not res:
            print("no matches")
        for r in res:
            srcs = ",".join(r["sources"]) or "(none)"
            print(f"[{r['_score']:.1f}] {r['term']}  conf={r['confidence']}  verified={r['last_verified']}  src={srcs}")
            print(f"      {r['definition'][:160]}")


if __name__ == "__main__":
    main()
