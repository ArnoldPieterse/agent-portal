#!/usr/bin/env python
# Lumen (Ca) - Mind-Lab smoke test: verify knowledge streams feed the portal.
# ---------------------------------------------------------------------------
# Idea seed (2026-11-26, world tick 2 / knowledge 12): each mind-lab "world tick"
# = one run of THIS script on a seat that can reach the portal. It proves the
# live data path: Archivist KB -> /api/*knowledge* endpoints -> portal -> UI.
#
# Stdlib only. No network on some seats (WinError 10013) -> exit 2 with a clear
# note, NOT a crash. Run:
#   python memory/designer/lumen/mindlab-knowledge-stream-smoke.py [--portal http://127.0.0.1:8099] [--root .]
import argparse, json, os, sys, time, urllib.request
from datetime import datetime

def get(url, timeout):
    t0 = time.time()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read().decode("utf-8", "replace")
            return {"ok": True, "status": r.status, "latency_ms": round((time.time()-t0)*1000),
                    "bytes": len(body), "body": body}
    except Exception as e:
        return {"ok": False, "status": None, "latency_ms": round((time.time()-t0)*1000),
                "error": repr(e)}

def count_kbs(b):
    # /api/knowledge-bases body -> best-effort integer count of streams
    try:
        d = json.loads(b)
    except Exception:
        return None
    if isinstance(d, list): return len(d)
    if isinstance(d, dict):
        for k in ("count", "total", "n"):
            if isinstance(d.get(k), int): return d[k]
        for v in d.values():
            if isinstance(v, list): return len(v)
    return None

def freshness(root, rel, max_h):
    p = os.path.join(root, rel)
    if not os.path.exists(p): return {"file": rel, "exists": False}
    age_h = (time.time() - os.path.getmtime(p)) / 3600.0
    return {"file": rel, "exists": True, "age_h": round(age_h,1),
            "stale": age_h > max_h, "size_kb": os.path.getsize(p)//1024}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--portal", default="http://127.0.0.1:8099")
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--timeout", type=int, default=8)
    ap.add_argument("--max-stale-h", type=float, default=24.0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    endpoints = ["/api/world", "/api/knowledge-bases", "/api/status"]
    streams, net_ok = {}, True
    for ep in endpoints:
        r = get(a.portal + ep, a.timeout)
        kb_count = count_kbs(r["body"]) if (ep == "/api/knowledge-bases" and r.get("ok")) else None
        rec = {k: v for k, v in r.items() if k != "body"}
        if ep == "/api/world":
            try: rec["payload"] = json.loads(r["body"])[:600] if r.get("ok") else None
            except Exception: pass
        if kb_count is not None: rec["kb_count"] = kb_count
        if not r.get("ok") and "10013" in r.get("error",""):
            rec["note"] = "socket blocked (WinError 10013): this seat has no portal network path"
        streams[ep] = rec
        net_ok = net_ok and r.get("ok", False)

    # knowledge source freshness (the upstream side of the stream)
    src_files = ["memory/archivist/knowledge-graph-v3.json",
                 "memory/archivist/semantic-index.json",
                 "memory/archivist/topic-heatmap.json",
                 "memory/archivist/kg_state.json"]
    sources = [freshness(a.root, f, a.max_stale_h) for f in src_files]

    any_stale = any(s.get("stale") for s in sources)
    report = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "portal": a.portal,
        "network_ok": net_ok,
        "streams": streams,
        "sources": sources,
        "any_source_stale": any_stale,
        "verdict": ("PASS" if net_ok else ("FAIL-NETWORK" if any("10013" in str(s.get("error","")) for s in streams.values()) else "FAIL-REACH")),
    }
    out = json.dumps(report, indent=2)
    print(out)
    dst = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "mindlab-stream-report.json")
    try:
        with open(dst, "w", encoding="utf-8") as f: f.write(out + "\n")
        print("\nwrote report ->", dst, file=sys.stderr)
    except Exception as e:
        print("\n(report write failed:", repr(e), ")", file=sys.stderr)
    # exit: 0 PASS, 1 reach-fail, 2 network-forbidden (seat constraint, not portal fault)
    sys.exit(0 if net_ok else (2 if any("10013" in str(s.get("error","")) for s in streams.values()) else 1))

if __name__ == "__main__":
    main()
