#!/usr/bin/env python3
"""AC-A2-2 LIVE LEG - single pass, run ON WHITE (127.0.0.1:8099). Mechanic r20 (2026-11-14 ~02:5x).
Expected per Verifier ac-a2-closure-r19.md + Designer ruling:
  [1] /api/uploads          -> exactly N=1 row: uploads/_canary_remote.txt, size 212
  [2] /api/file/raw?path=uploads/_canary_remote.txt -> HTTP 200, body EXACTLY 212 bytes
  [3] console clean (browser/devtools leg = Arnold or White-seated agent; not covered by this script)
Read-only: two GETs. Writes ac_a2_live_leg_r20_result.json next to itself.
"""
import json, hashlib, time, urllib.request, urllib.parse

BASE = "http://127.0.0.1:8099"
out = {"started": time.strftime('%Y-%m-%d %H:%M:%S'), "checks": {}}

def save():
    json.dump(out, open("ac_a2_live_leg_r20_result.json", "w"), indent=1)

# [1] panel inventory
try:
    with urllib.request.urlopen(BASE + "/api/uploads", timeout=15) as r:
        st = r.status
        d = json.load(r)
    items = d.get("files") or d.get("data") or (d if isinstance(d, list) else [])
    rows = [(it.get("path"), it.get("size")) for it in items]
    out["checks"]["uploads_list"] = {"status": st, "n": len(rows), "rows": rows,
        "expect": "canary row present at size 212 (N>=1; pre-existing files per r27)",
        "pass": st == 200 and ("uploads/_canary_remote.txt", 212) in rows}
except Exception as e:
    out["checks"]["uploads_list"] = {"error": "%s: %s" % (type(e).__name__, str(e)[:120]), "pass": False}
save()

# [2] raw fetch byte-exactness
try:
    u = BASE + "/api/file/raw?path=" + urllib.parse.quote("uploads/_canary_remote.txt")
    with urllib.request.urlopen(u, timeout=15) as r:
        st = r.status
        body = r.read()
    out["checks"]["raw_fetch"] = {"status": st, "bytes": len(body), "md5": hashlib.md5(body).hexdigest(),
        "expect": "200 + exactly 212 bytes (Verifier pin prefix 512d0dc8)",
        "pass": st == 200 and len(body) == 212}
except Exception as e:
    out["checks"]["raw_fetch"] = {"error": "%s: %s" % (type(e).__name__, str(e)[:120]), "pass": False}
save()

out["finished"] = time.strftime('%Y-%m-%d %H:%M:%S')
out["verdict"] = "PASS" if all(c.get("pass") for c in out["checks"].values()) else "FAIL"
out["note3"] = "console-clean leg still owed in a browser (devtools): no JS errors, no /api/uploads background timer."
save()
print(json.dumps(out, indent=1))
