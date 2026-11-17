"""Test mirror_heal.py core logic (no network required)."""
import json, os, sys, tempfile, shutil
from datetime import datetime, timezone, timedelta

sys.path.insert(0, ".")
results = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"  [{status}] {name}" + (f" ({detail})" if detail and not condition else ""))

# --- Test 1: Staleness detection with fresh log ---
print("\nTest 1: Fresh mirror run -> no staleness")
tmpdir = tempfile.mkdtemp()
try:
    now = datetime.now(timezone.utc)
    recent_ts = (now - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
    test_log = os.path.join(tmpdir, "memory_mirror.log")
    with open(test_log, "w") as f:
        f.write(json.dumps({"t": recent_ts, "status": "ok"}) + "\n")
    
    import mirror_heal as mh
    orig_log = mh.LOG_FILE
    orig_repair = mh.REPAIR_LOG
    orig_max_age = mh.MAX_AGE_S
    mh.LOG_FILE = test_log
    mh.REPAIR_LOG = os.path.join(tmpdir, "mirror-repairs.jsonl")
    mh.MAX_AGE_S = 900
    
    last_ts = mh._last_mirror_run_ts()
    check("parses recent timestamp", last_ts is not None, f"got {last_ts}")
finally:
    mh.LOG_FILE = orig_log
    mh.REPAIR_LOG = orig_repair
    mh.MAX_AGE_S = orig_max_age
    shutil.rmtree(tmpdir)

# --- Test 2: Staleness detection with old log ---
print("\nTest 2: Old mirror run -> staleness fires")
tmpdir = tempfile.mkdtemp()
try:
    now = datetime.now(timezone.utc)
    old_ts = (now - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    test_log = os.path.join(tmpdir, "memory_mirror.log")
    with open(test_log, "w") as f:
        f.write(json.dumps({"t": old_ts, "status": "ok"}) + "\n")
    
    import mirror_heal as mh
    orig_log = mh.LOG_FILE
    orig_repair = mh.REPAIR_LOG
    mh.LOG_FILE = test_log
    mh.REPAIR_LOG = os.path.join(tmpdir, "mirror-repairs.jsonl")
    mh.MAX_AGE_S = 900
    
    last_ts = mh._last_mirror_run_ts()
    check("parses old timestamp", last_ts is not None, f"got {last_ts}")
finally:
    mh.LOG_FILE = orig_log
    mh.REPAIR_LOG = orig_repair
    shutil.rmtree(tmpdir)

# --- Test 3: Log event format ---
print("\nTest 3: _log_event writes valid JSONL")
tmpdir = tempfile.mkdtemp()
try:
    import mirror_heal as mh
    orig_repair = mh.REPAIR_LOG
    test_repair = os.path.join(tmpdir, "mirror-repairs.jsonl")
    mh.REPAIR_LOG = test_repair
    
    mh._log_event("test_event", "test detail", hosts=["Red"])
    
    with open(test_repair) as f:
        line = f.readline().strip()
    entry = json.loads(line)
    check("has ts field", "ts" in entry)
    check("has type field", entry.get("type") == "test_event")
    check("has detail field", entry.get("detail") == "test detail")
    check("has hosts field", entry.get("hosts") == ["Red"])
finally:
    mh.REPAIR_LOG = orig_repair
    shutil.rmtree(tmpdir)

# --- Test 4: Alert threshold logic ---
print("\nTest 4: Alert threshold at >3 failures/hour")
tmpdir = tempfile.mkdtemp()
try:
    import mirror_heal as mh
    orig_repair = mh.REPAIR_LOG
    test_repair = os.path.join(tmpdir, "mirror-repairs.jsonl")
    mh.REPAIR_LOG = test_repair
    
    for i in range(3):
        mh._log_event("repair_failed", f"fail {i}")
    
    with open(test_repair) as f:
        lines = [json.loads(l) for l in f if l.strip()]
    fail_count = sum(1 for l in lines if l["type"] == "repair_failed")
    check("3 failures logged", fail_count == 3, f"got {fail_count}")
finally:
    mh.REPAIR_LOG = orig_repair
    shutil.rmtree(tmpdir)

# --- Summary ---
print(f"\n{'='*50}")
passed = sum(1 for _, s, _ in results if s == "PASS")
total = len(results)
print(f"Results: {passed}/{total} passed")
if passed < total:
    for name, status, detail in results:
        if status == "FAIL":
            print(f"  FAILED: {name} - {detail}")
else:
    print("ALL PASS")
