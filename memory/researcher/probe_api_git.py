#!/usr/bin/env python3
"""researcher/probe_api_git.py - probe for GET /api/git + POST /api/git (Researcher goal).
Re-usable by Verifier. Run from anywhere:  python memory/researcher/probe_api_git.py

EXPECTED OUTPUTS (documented):
  GET /api/git   -> 200 {"repo": true, "changed": <int>, "status": "<porcelain text>", "log": "<last 12 oneline>"}
                    if no .git: {"repo": false, "note": "run POST /api/git {action:'init'} first"}
  POST /api/git {"action":"commit","message":"..."} -> 200 {"ok": true, "committed": <bool>, "out": "[main <hash>] <msg> ..."}
                    message required: empty/missing -> 400 {"error": "message required"}
  POST /api/git {"action":"init"} -> 200 {"ok": true, "status": {...}} (creates repo + local identity)
Exit 0 = all probes PASS.
"""
import json, sys, urllib.request, urllib.error

B = "http://127.0.0.1:8099"
fails = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond: fails.append(name)

def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(B + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(r, timeout=30)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read())
        except Exception: return e.code, {}

# 1) GET status
st, d = req("GET", "/api/git")
check("GET /api/git -> 200", st == 200, str(st))
check("GET has repo/changed/status/log keys", all(k in d for k in ("repo", "changed", "status", "log")), str(d)[:120])
check("repo is true (workspace has .git)", d.get("repo") is True)

# 2) POST commit with message
st, d = req("POST", "/api/git", {"action": "commit", "message": "probe: api_git probe run (researcher goal 6)"})
check("POST commit -> 200 ok", st == 200 and d.get("ok") is True, str(d)[:150])
check("POST commit out carries [main <hash>]", "[main" in d.get("out", ""), str(d.get("out", ""))[:120])

# 3) POST commit without message -> 400
st, d = req("POST", "/api/git", {"action": "commit"})
check("POST empty message -> 400", st == 400 and "message required" in d.get("error", ""), f"{st} {str(d)[:80]}")

# 4) GET reflects the new commit on top
st, d = req("GET", "/api/git")
check("GET log head shows probe commit", "probe: api_git probe run" in d.get("log", ""), d.get("log", "")[:120])

print()
if fails:
    print(f"RESULT: FAIL ({len(fails)}): {fails}"); sys.exit(1)
print("RESULT: ALL PASS (7/7 probes)")
