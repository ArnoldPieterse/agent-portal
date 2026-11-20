#!/usr/bin/env python3
"""Selftest for mirror_heal.py - verifies alert threshold logic.

Tests:
1. Fresh mirror -> no action
2. Stale mirror + 0 prior failures -> repair attempted, no alert
3. Stale mirror + 3 prior failures -> repair attempted, no alert (threshold is >3)
4. Stale mirror + 4 prior failures -> repair attempted, ALERT fires
5. No mirror log -> repair_failed logged

Run: python memory/mechanic/goal2_mirror_heal_selftest.py
"""
import json, os, sys, tempfile, shutil, datetime
from unittest.mock import patch, MagicMock

# Add the ops dir to path so we can import mirror_heal
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ops"))

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} {detail}")

def make_log_entry(ts_str, **kwargs):
    entry = {"t": ts_str}
    entry.update(kwargs)
    return json.dumps(entry)

def write_mirror_log(path, entries):
    with open(path, "w") as f:
        for e in entries:
            f.write(e + "\n")

def write_repair_log(path, entries):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

def read_repair_log(path):
    if not os.path.exists(path):
        return []
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries

def run_test(name, setup_fn, verify_fn):
    print(f"\nTest: {name}")
    tmpdir = tempfile.mkdtemp(prefix="mirror_heal_test_")
    try:
        mirror_log = os.path.join(tmpdir, "memory_mirror.log")
        repair_log = os.path.join(tmpdir, "memory", "mechanic", "mirror-repairs.jsonl")
        mirror_script = os.path.join(tmpdir, "memory_mirror.py")
        
        # Create a dummy mirror script that succeeds
        with open(mirror_script, "w") as f:
            f.write("import sys; sys.exit(0)")
        
        setup_fn(mirror_log, repair_log)
        
        # Patch paths in mirror_heal
        import importlib
        if "mirror_heal" in sys.modules:
            del sys.modules["mirror_heal"]
        import mirror_heal
        mirror_heal.MIRROR_LOG = mirror_log
        mirror_heal.REPAIR_LOG = repair_log
        mirror_heal.MIRROR_SCRIPT = mirror_script
        mirror_heal.HERE = tmpdir
        
        # Run main (not dry-run)
        sys.argv = ["mirror_heal.py"]  # no --dry-run
        mirror_heal.DRY_RUN = False
        mirror_heal.main()
        
        verify_fn(repair_log, tmpdir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# --- Test 1: Fresh mirror -> no action ---
def setup_fresh(mirror_log, repair_log):
    now = datetime.datetime.now(datetime.timezone.utc)
    ts = now.strftime("%Y-%m-%d %H:%M:%S")
    write_mirror_log(mirror_log, [make_log_entry(ts)])

def verify_fresh(repair_log, tmpdir):
    entries = read_repair_log(repair_log)
    check("no repair log entries", len(entries) == 0, f"got {len(entries)}")

# --- Test 2: Stale + 0 failures -> repair_ok, no alert ---
def setup_stale_0(mirror_log, repair_log):
    old = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    ts = old.strftime("%Y-%m-%d %H:%M:%S")
    write_mirror_log(mirror_log, [make_log_entry(ts)])

def verify_stale_0(repair_log, tmpdir):
    entries = read_repair_log(repair_log)
    check("1 entry logged", len(entries) == 1, f"got {len(entries)}")
    if entries:
        e = entries[0]
        check("type is repair_ok", e.get("type") == "repair_ok", f"got {e.get('type')}")
        check("no ALERT key", "ALERT" not in e)

# --- Test 3: Stale + 3 prior failures -> repair_ok, no alert (threshold >3) ---
def setup_stale_3(mirror_log, repair_log):
    old = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    ts = old.strftime("%Y-%m-%d %H:%M:%S")
    write_mirror_log(mirror_log, [make_log_entry(ts)])
    # Write 3 recent failures
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    entries = []
    for i in range(3):
        entries.append({"ts": now_iso, "type": "repair_failed", "detail": f"sim failure {i}"})
    write_repair_log(repair_log, entries)

def verify_stale_3(repair_log, tmpdir):
    entries = read_repair_log(repair_log)
    # 3 pre-existing + 1 new = 4 total
    check("4 total entries", len(entries) == 4, f"got {len(entries)}")
    if len(entries) >= 4:
        e = entries[3]  # newest
        check("new entry is repair_ok", e.get("type") == "repair_ok", f"got {e.get('type')}")
        check("no ALERT (exactly 3, threshold is >3)", "ALERT" not in e)

# --- Test 4: Stale + 4 prior failures + repair ALSO fails -> ALERT fires ---
def run_test_4():
    print(f"\\nTest: Stale + 4 prior failures + repair fails -> ALERT fires")
    tmpdir = tempfile.mkdtemp(prefix="mirror_heal_test4_")
    try:
        mirror_log = os.path.join(tmpdir, "memory_mirror.log")
        repair_log = os.path.join(tmpdir, "memory", "mechanic", "mirror-repairs.jsonl")
        mirror_script = os.path.join(tmpdir, "memory_mirror.py")
        
        # Failing script
        with open(mirror_script, "w") as f:
            f.write("import sys; print('still broken', file=sys.stderr); sys.exit(1)")
        
        old = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        ts = old.strftime("%Y-%m-%d %H:%M:%S")
        write_mirror_log(mirror_log, [make_log_entry(ts)])
        # 4 prior failures in last hour
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        entries = []
        for i in range(4):
            entries.append({"ts": now_iso, "type": "repair_failed", "detail": f"sim failure {i}"})
        write_repair_log(repair_log, entries)
        
        import importlib
        if "mirror_heal" in sys.modules:
            del sys.modules["mirror_heal"]
        import mirror_heal
        mirror_heal.MIRROR_LOG = mirror_log
        mirror_heal.REPAIR_LOG = repair_log
        mirror_heal.MIRROR_SCRIPT = mirror_script
        mirror_heal.HERE = tmpdir
        
        sys.argv = ["mirror_heal.py"]
        mirror_heal.DRY_RUN = False
        mirror_heal.main()
        
        entries = read_repair_log(repair_log)
        # 4 pre-existing + 1 new = 5 total
        check("5 total entries", len(entries) == 5, f"got {len(entries)}")
        if len(entries) >= 5:
            e = entries[4]  # newest
            check("type is repair_failed", e.get("type") == "repair_failed", f"got {e.get('type')}")
            check("failures_last_hour = 5", e.get("failures_last_hour") == 5, f"got {e.get('failures_last_hour')}")
            check("ALERT is True", e.get("ALERT") is True)
            check("alert_msg present", "alert_msg" in e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# --- Test 5: No mirror log -> repair_failed ---
def setup_no_log(mirror_log, repair_log):
    # Don't create the file
    pass

def verify_no_log(repair_log, tmpdir):
    entries = read_repair_log(repair_log)
    check("1 entry logged", len(entries) == 1, f"got {len(entries)}")
    if entries:
        e = entries[0]
        check("type is repair_failed", e.get("type") == "repair_failed", f"got {e.get('type')}")

# --- Test 6: Stale + mirror script fails -> repair_failed with error ---
def setup_stale_fail(mirror_log, repair_log):
    old = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    ts = old.strftime("%Y-%m-%d %H:%M:%S")
    write_mirror_log(mirror_log, [make_log_entry(ts)])

def verify_stale_fail(repair_log, tmpdir):
    entries = read_repair_log(repair_log)
    check("1 entry logged", len(entries) == 1, f"got {len(entries)}")
    if entries:
        e = entries[0]
        check("type is repair_failed", e.get("type") == "repair_failed", f"got {e.get('type')}")

# Override test 6 to use a failing script
def run_test_6():
    print(f"\nTest: Stale + mirror script fails -> repair_failed")
    tmpdir = tempfile.mkdtemp(prefix="mirror_heal_test6_")
    try:
        mirror_log = os.path.join(tmpdir, "memory_mirror.log")
        repair_log = os.path.join(tmpdir, "memory", "mechanic", "mirror-repairs.jsonl")
        mirror_script = os.path.join(tmpdir, "memory_mirror.py")
        
        # Failing script
        with open(mirror_script, "w") as f:
            f.write("import sys; print('boom', file=sys.stderr); sys.exit(1)")
        
        old = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
        ts = old.strftime("%Y-%m-%d %H:%M:%S")
        write_mirror_log(mirror_log, [make_log_entry(ts)])
        
        import importlib
        if "mirror_heal" in sys.modules:
            del sys.modules["mirror_heal"]
        import mirror_heal
        mirror_heal.MIRROR_LOG = mirror_log
        mirror_heal.REPAIR_LOG = repair_log
        mirror_heal.MIRROR_SCRIPT = mirror_script
        mirror_heal.HERE = tmpdir
        
        sys.argv = ["mirror_heal.py"]
        mirror_heal.DRY_RUN = False
        mirror_heal.main()
        
        entries = read_repair_log(repair_log)
        check("1 entry logged", len(entries) == 1, f"got {len(entries)}")
        if entries:
            e = entries[0]
            check("type is repair_failed", e.get("type") == "repair_failed", f"got {e.get('type')}")
            check("detail contains error", "boom" in e.get("detail", ""), f"got {e.get('detail','')[:50]}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# Run all tests
print("=" * 60)
print("mirror_heal.py selftest - alert threshold verification")
print("=" * 60)

run_test("Fresh mirror -> no action", setup_fresh, verify_fresh)
run_test("Stale + 0 failures -> repair_ok, no alert", setup_stale_0, verify_stale_0)
run_test("Stale + 3 failures -> repair_ok, no alert (boundary)", setup_stale_3, verify_stale_3)
run_test_4()
run_test("No mirror log -> repair_failed", setup_no_log, verify_no_log)
run_test_6()

print(f"\n{'=' * 60}")
print(f"RESULT: {PASS} PASS / {FAIL} FAIL out of {PASS+FAIL}")
if FAIL == 0:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")
sys.exit(1 if FAIL else 0)
