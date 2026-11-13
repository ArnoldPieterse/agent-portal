#!/usr/bin/env python3
"""AC-A2-2 LIVE LEG r21 - single pass, run ON WHITE (127.0.0.1:8099). Verifier r29 restage (2026-11-14 ~05:5x).
Supersedes ac_a2_live_leg_r20.py semantics per Verifier ruling memory/verifier/r28-probe-check1-ratification.md:
  [1] /api/uploads -> PASS = status 200 AND canary row ('uploads/_canary_remote.txt', 212) PRESENT (N>=1;
      handler walks recursively, files only - N=1 was a clean-room convenience assumption, not AC-A2 semantics).
  [2] /api/file/raw?path=uploads/_canary_remote.txt -> HTTP 200 + body EXACTLY 212 bytes
      + md5 == 512d0dc8e96773b7db5574da4f0ae9f3 (full pin, tightened from prefix).
  [3] console clean = browser/devtools leg (Arnold or White-seated agent); criteria in
      memory/designer/ac-a2-2-console-clean-criteria.md. NOT covered by this script.
Read-only: two GETs. Writes ac_a2_live_leg_r21_result.json next to itself.
Self-test (any seat, no network): python ac_a2_live_leg_r21.py --selftest
"""
import json, hashlib, time, sys, urllib.request, urllib.parse

BASE = "http://127.0.0.1:8099"
CANARY = ("uploads/_canary_remote.txt", 212)
CANARY_MD5 = "512d0dc8e96773b7db5574da4f0ae9f3"
out = {"started": time.strftime('%Y-%m-%d %H:%M:%S'), "checks": {}}

def save():
    json.dump(out, open("ac_a2_live_leg_r21_result.json", "w"), indent=1)

def check_uploads(st, rows):
    return {"status": st, "n": len(rows), "rows": rows,
        "expect": "200 + canary row present (N>=1): ('uploads/_canary_remote.txt', 212)",
        "pass": st == 200 and CANARY in rows}

def check_raw(st, body):
    return {"status": st, "bytes": len(body), "md5": hashlib.md5(body).hexdigest(),
        "expect": "200 + exactly 212 bytes + md5 512d0dc8e96773b7db5574da4f0ae9f3",
        "pass": st == 200 and len(body) == 212 and hashlib.md5(body).hexdigest() == CANARY_MD5}

if "--selftest" in sys.argv:
    # offline logic proof: expected payload passes; adversarial payloads fail
    ok_rows = [CANARY, ("uploads/projects\x00junk", 10)]
    # canary body from the on-disk artifact (byte-exact per sweep); proves pin matches reality
    canary_body = None
    for cand in ("uploads/_canary_remote.txt", "memory/verifier/_canary_remote.txt"):
        try:
            b = open(cand, "rb").read()
            if hashlib.md5(b).hexdigest() == CANARY_MD5:
                canary_body = b
                break
        except OSError:
            pass
    assert canary_body is not None and len(canary_body) == 212, "canary pin self-check failed (no artifact matching %s)" % CANARY_MD5
    assert check_uploads(200, ok_rows)["pass"] is True
    assert check_uploads(200, [("uploads/other.txt", 5)])["pass"] is False
    assert check_uploads(404, ok_rows)["pass"] is False
    assert check_raw(200, canary_body)["pass"] is True
    assert check_raw(200, canary_body[:-1])["pass"] is False
    assert check_raw(500, canary_body)["pass"] is False
    print("SELFTEST PASS: 6/6 assertions (canary pin + 5 verdict cases)")
    sys.exit(0)

# [1] panel inventory
try:
    with urllib.request.urlopen(BASE + "/api/uploads", timeout=15) as r:
        st = r.status
        d = json.load(r)
    items = d.get("files") or d.get("data") or (d if isinstance(d, list) else [])
    rows = [(it.get("path"), it.get("size")) for it in items]
    out["checks"]["uploads_list"] = check_uploads(st, rows)
except Exception as e:
    out["checks"]["uploads_list"] = {"error": "%s: %s" % (type(e).__name__, str(e)[:120]), "pass": False}
save()

# [2] raw fetch byte-exactness
try:
    u = BASE + "/api/file/raw?path=" + urllib.parse.quote("uploads/_canary_remote.txt")
    with urllib.request.urlopen(u, timeout=15) as r:
        st = r.status
        body = r.read()
    out["checks"]["raw_fetch"] = check_raw(st, body)
except Exception as e:
    out["checks"]["raw_fetch"] = {"error": "%s: %s" % (type(e).__name__, str(e)[:120]), "pass": False}
save()

out["finished"] = time.strftime('%Y-%m-%d %H:%M:%S')
out["verdict"] = "PASS" if all(c.get("pass") for c in out["checks"].values()) else "FAIL"
out["note3"] = "console-clean leg still owed in a browser (devtools) per memory/designer/ac-a2-2-console-clean-criteria.md."
save()
print(json.dumps(out, indent=1))
