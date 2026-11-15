#!/usr/bin/env python3
"""CHG-0002 pre-written tests: /api/evolution endpoints in agent_portal.py.
Run AFTER portal restart (restart-trap check is test 3).
Usage: python memory/verifier/chg0002_tests.py [PORTAL_URL]
Default: http://127.0.0.1:8099
"""
import json, sys, time, urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8099"
PASS = 0
FAIL = 0

def get(path):
    req = urllib.request.Request(BASE + path)
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, json.loads(r.read())

def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def check(label, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS: {label}")
    else:
        FAIL += 1
        print(f"  FAIL: {label} {detail}")

print("=== CHG-0002 Tests ===")
print(f"Portal: {BASE}")

# --- TEST 1: GET /api/evolution/stats returns ok:true with correct shape ---
print("\n[TEST 1] GET /api/evolution/stats")
try:
    status, data = get("/api/evolution/stats")
    check("HTTP 200", status == 200, f"got {status}")
    check("ok=true", data.get("ok") is True, f"got {data.get('ok')}")
    check("has island field", "island" in data)
    check("has living count (int)", isinstance(data.get("living"), int))
    check("has candidates count (int)", isinstance(data.get("candidates"), int))
    check("has dead count (int)", isinstance(data.get("dead"), int))
    check("has changes list", isinstance(data.get("changes"), list))
    check("has graveyard list", isinstance(data.get("graveyard"), list))
    # Verify CHG-0001 is living
    chg1 = next((c for c in data.get("changes", []) if c["id"] == "CHG-0001"), None)
    check("CHG-0001 present", chg1 is not None)
    check("CHG-0001 status=living", chg1 and chg1.get("status") == "living")
    # Verify CHG-0002 is candidate
    chg2 = next((c for c in data.get("changes", []) if c["id"] == "CHG-0002"), None)
    check("CHG-0002 present", chg2 is not None)
    check("CHG-0002 status=candidate", chg2 and chg2.get("status") == "candidate")
except Exception as e:
    check("no exception", False, str(e))

# --- TEST 2: POST /api/evolution/reject with invalid id returns 400 ---
print("\n[TEST 2] POST /api/evolution/reject (invalid id -> 400)")
try:
    status, data = post("/api/evolution/reject", {"id": "BAD-ID", "cause": "test"})
    check("HTTP 400 for bad id format", status == 400, f"got {status}")
    check("error message present", "error" in data)
except Exception as e:
    check("no exception", False, str(e))

# --- TEST 3: Restart trap - engine reloads cleanly after portal restart ---
print("\n[TEST 3] Restart trap (engine loads fresh after portal restart)")
print("  NOTE: This test requires the portal to have been restarted since evolution.py")
print("  was first deployed. Verify _portal_pid.txt CreationDate > evolution.py mtime.")
try:
    # First call - should work
    status1, data1 = get("/api/evolution/stats")
    check("first call ok", status1 == 200 and data1.get("ok") is True)
    # Second call immediately after (tests module cache path)
    time.sleep(0.1)
    status2, data2 = get("/api/evolution/stats")
    check("second call ok (cached module)", status2 == 200 and data2.get("ok") is True)
    check("consistent island name", data1.get("island") == data2.get("island"))
    # The real restart-trap check: verify the portal PID file mtime > evolution.py mtime
    import os
    pid_file = "_portal_pid.txt"
    evo_file = "evolution.py"
    if os.path.exists(pid_file) and os.path.exists(evo_file):
        pid_mtime = os.path.getmtime(pid_file)
        evo_mtime = os.path.getmtime(evo_file)
        check("portal started after evolution.py deployed", pid_mtime >= evo_mtime,
              f"pid_file={time.ctime(pid_mtime)} evo={time.ctime(evo_mtime)}")
    else:
        print(f"  SKIP: {pid_file} or {evo_file} not found in cwd (run from portal root)")
except Exception as e:
    check("no exception", False, str(e))

print(f"\n=== RESULTS: {PASS} pass / {FAIL} fail ===")
sys.exit(1 if FAIL else 0)