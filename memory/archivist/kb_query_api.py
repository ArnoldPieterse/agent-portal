#!/usr/bin/env python3
"""kb_query_api.py - Archivist Goal 1 (cycle-13): Cockpit Knowledge Query API.

Answers "what does the KB say about <query>" by combining three existing
building blocks:
  * kb_search.score_query      -> ranked leaves (TF-IDF over memory/*.md)
  * provenance-ledger.json     -> per-fact provenance chain + confidence
  * file mtime                 -> freshness tier (deterministic, age-based)

Each answer leaf: {file, title, confidence, freshness, provenance_chain}.

Run modes:
  python memory/archivist/kb_query_api.py --selftest        # headless verify (exit 0/1)
  python memory/archivist/kb_query_api.py --serve [--port 8096]
  GET /query?q=<text>&limit=N   -> JSON
  GET /health                   -> {ok:true, port, index_docs}
"""
import json, os, sys, time, math
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kb_search  # same-dir module: score_query(q) -> [{path,title,score,...}]

ROOT = os.path.dirname(os.path.dirname(HERE))
LEDGER = os.path.join(HERE, "provenance-ledger.json")
PORT_DEFAULT = 8096

# --- freshness (deterministic, mtime-based; distinct from score quarantine) ---
def freshness(mtime):
    age_days = max(0.0, (time.time() - mtime) / 86400.0)
    if age_days < 7:   return 1.0, "fresh"
    if age_days < 30:  return 0.8, "recent"
    if age_days < 90:  return 0.5, "aging"
    return 0.2, "stale"

_prov_cache = {"ts": 0.0, "by_file": None}
def load_provenance(force=False):
    now = time.time()
    if not force and _prov_cache["by_file"] is not None and now - _prov_cache["ts"] < 60:
        return _prov_cache["by_file"]
    by_file = {}
    try:
        ledger = json.loads(open(LEDGER, encoding="utf-8").read())
    except Exception:
        return {}
    for f in ledger.get("facts", []):
        by_file.setdefault(f["source_file"], []).append(f)
    # precompute max confidence per file for fast lookup
    _prov_cache.update(ts=now, by_file=by_file)
    return by_file

def _chain_for(path, title, facts):
    """Resolvable provenance chain = facts whose source line was found (status verified)."""
    resolvable = [f for f in facts if f.get("line") is not None and f.get("status") == "verified"]
    # prefer the fact matching the leaf's H1 title, then rank by confidence
    def key(f):
        val = (f.get("value") or "").strip().lower()
        t = (title or "").strip().lower()
        return (0 if (t and (val == t or (len(t) > 5 and t in val))) else 1, -f.get("confidence", 0))
    resolvable.sort(key=key)
    chain = [{"fact_id": f["fact_id"], "line": f["line"], "extraction_rule": f["extraction_rule"],
              "value": f.get("value"), "confidence": f.get("confidence"), "status": f.get("status")}
             for f in resolvable[:8]]
    conf = max((f.get("confidence", 0.0) for f in resolvable), default=0.0)
    return chain, round(conf, 3)

def answer(query, limit=5):
    """Pure, headlessly-testable core: combine search + provenance + freshness."""
    t0 = time.time()
    by_file = load_provenance()
    hits = kb_search.score_query(query)[:max(1, limit)]
    leaves = []
    for h in hits:
        facts = by_file.get(h["path"], [])
        chain, conf = _chain_for(h["path"], h["title"], facts)
        mtime = os.path.getmtime(os.path.join(ROOT, h["path"])) if os.path.exists(os.path.join(ROOT, h["path"])) else time.time()
        fscore, ftier = freshness(mtime)
        leaves.append({
            "file": h["path"], "title": h["title"], "score": h.get("score"),
            "confidence": conf, "freshness": round(fscore, 2), "freshness_tier": ftier,
            "resolvable": len(chain) > 0,
            "provenance_chain": chain,
        })
    return {"query": query, "count": len(leaves), "answer_leaves": leaves,
            "elapsed_ms": round((time.time() - t0) * 1000.0, 2)}

# --- selftest: the four verification criteria from the goal card ---
def selftest():
    print("kb_query_api --selftest")
    ok = True
    # warm the index once (one-time cold build is not steady-state latency)
    kb_search.build_index()
    # (1) a real query returns >=1 leaf with a resolvable provenance chain
    r1 = answer("provenance ledger freshness", limit=5)
    c1 = any(l["resolvable"] and l["provenance_chain"] for l in r1["answer_leaves"])
    print("  [1] >=1 leaf w/ resolvable chain: %s (count=%d, elapsed=%sms)" %
          ("PASS" if c1 else "FAIL", r1["count"], r1["elapsed_ms"]))
    ok &= c1
    # (2) steady-state response < 500ms on the live (warm) index
    fast = r1["elapsed_ms"] < 500.0
    print("  [2] response <500ms (warm): %s (%sms)" % ("PASS" if fast else "FAIL", r1["elapsed_ms"]))
    ok &= fast
    # (3) idempotent: same query -> same ranked file set (real-term query, non-empty)
    a = [l["file"] for l in answer("provenance confidence extraction rule", limit=5)["answer_leaves"]]
    b = [l["file"] for l in answer("provenance confidence extraction rule", limit=5)["answer_leaves"]]
    c3 = (a == b) and len(a) > 0
    print("  [3] idempotent ranked set: %s (%d leaves, equal=%s)" % ("PASS" if c3 else "FAIL", len(a), a == b))
    ok &= c3
    # (4) graceful empty for unknown topics (no crash)
    try:
        r4 = answer("zzqx blorpt unfoundtopic 9x7", limit=5)
        c4 = (r4["count"] == 0) and (r4["answer_leaves"] == [])
    except Exception as e:
        print("  [4] graceful empty: FAIL (raised %s)" % e); ok = False; return ok
    print("  [4] graceful empty result: %s (count=%d)" % ("PASS" if c4 else "FAIL", r4["count"]))
    ok &= c4
    print("SELFTEST: " + ("PASS" if ok else "FAIL"))
    return ok

# --- HTTP server ---
def serve(port=PORT_DEFAULT):
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlparse, parse_qs
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _send(self, obj, code=200):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            u = urlparse(self.path); q = parse_qs(u.query)
            if u.path == "/health":
                return self._send({"ok": True, "port": port, "index_docs": kb_search.build_index()["N"]})
            if u.path == "/query":
                text = (q.get("q", [""])[0]).strip()
                limit = int(q.get("limit", ["5"])[0])
                if not text: return self._send({"error": "missing q"}, 400)
                return self._send(answer(text, limit))
            return self._send({"error": "not found"}, 404)
    srv = HTTPServer(("127.0.0.1", port), H)
    print("kb_query_api serving on http://127.0.0.1:%d/query?q=... (Ctrl-C to stop)" % port)
    try: srv.serve_forever()
    except KeyboardInterrupt: pass

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    elif "--serve" in sys.argv:
        p = PORT_DEFAULT
        if "--port" in sys.argv: p = int(sys.argv[sys.argv.index("--port") + 1])
        serve(p)
    else:
        print(__doc__)