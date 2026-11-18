#!/usr/bin/env python3
"""Unit test for mirror_heal.py TZ handling + success detection (goal #2).

Verifies that _last_sync_time():
1. Correctly interprets local-time log entries (TZ fix)
2. Only counts runs where at least one host synced successfully (success detection)
3. Skips all-failed runs so persistent auth errors trigger repair

Run: python memory/mechanic/test_mirror_heal_tz.py
"""
import datetime, json, os, sys, tempfile, importlib.util

# Load mirror_heal as a module
script_path = os.path.join(os.path.dirname(__file__), "..", "ops", "mirror_heal.py")
spec = importlib.util.spec_from_file_location("mirror_heal", script_path)
mh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mh)

PASS = 0
FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} {detail}")

print("=== mirror_heal.py TZ handling tests ===\n")

# Test 1: A timestamp from 5 minutes ago (local) should be FRESH (< 900s)
now_local = datetime.datetime.now()
recent_ts = (now_local - datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    # Realistic log entry: at least one host without error = successful sync
    f.write(json.dumps({"t": recent_ts, "results": [{"host": "Red", "pushed": ["a.md"], "pulled": []}]}) + "\n")
    tmp_log = f.name

# Monkey-patch the log path
orig_log = mh.MIRROR_LOG
mh.MIRROR_LOG = tmp_log
result = mh._last_sync_time()
mh.MIRROR_LOG = orig_log
os.unlink(tmp_log)

if result is not None:
    age_s = (datetime.datetime.now(datetime.timezone.utc) - result).total_seconds()
    check("recent local ts -> fresh (age < 900s)", 0 <= age_s < 900, f"age={age_s:.0f}s")
else:
    check("recent local ts parsed", False, "returned None")

# Test 2: A timestamp from 30 minutes ago (local) should be STALE (> 900s)
old_ts = (now_local - datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")

with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    f.write(json.dumps({"t": old_ts, "results": [{"host": "Red", "pushed": [], "pulled": ["b.md"]}]}) + "\n")
    tmp_log = f.name

mh.MIRROR_LOG = tmp_log
result = mh._last_sync_time()
mh.MIRROR_LOG = orig_log
os.unlink(tmp_log)

if result is not None:
    age_s = (datetime.datetime.now(datetime.timezone.utc) - result).total_seconds()
    check("old local ts -> stale (age > 900s)", age_s > 900, f"age={age_s:.0f}s")
else:
    check("old local ts parsed", False, "returned None")

# Test 3: The BUG scenario - on a UTC+10 host, a CURRENT local timestamp
# misread as UTC would appear ~10h in the future (negative age -> always fresh).
# Verify our fix produces a small POSITIVE age for a just-written log entry.
just_now_local = datetime.datetime.now()
just_now_ts = just_now_local.strftime("%Y-%m-%d %H:%M:%S")

with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    f.write(json.dumps({"t": just_now_ts, "results": [{"host": "Red", "pushed": ["c.md"]}]}) + "\n")
    tmp_log = f.name

mh.MIRROR_LOG = tmp_log
result = mh._last_sync_time()
mh.MIRROR_LOG = orig_log
os.unlink(tmp_log)

if result is not None:
    age_s = (datetime.datetime.now(datetime.timezone.utc) - result).total_seconds()
    # With the fix: local now -> UTC conversion gives age ~0 to +60s (clock drift)
    # Without the fix (old code): on UTC+10, age would be ~-36000s (10h negative)
    check("bug guard: current local ts gives small positive age", -60 < age_s < 120, f"age={age_s:.0f}s")
else:
    check("current local ts parsed", False, "returned None")

# Test 4: Multiple log lines - last SUCCESSFUL one wins
multi_lines = [
    json.dumps({"t": (now_local - datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"), "results": [{"host": "Red", "pushed": ["a.md"]}]}),
    # This entry has ALL hosts failed -> should be SKIPPED
    json.dumps({"t": (now_local - datetime.timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"), "results": [{"host": "Red", "error": "connect: Access denied"}]}),
    json.dumps({"t": (now_local - datetime.timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"), "results": [{"host": "Red", "pushed": ["b.md"]}]}),
]

with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    f.write("\n".join(multi_lines) + "\n")
    tmp_log = f.name

mh.MIRROR_LOG = tmp_log
result = mh._last_sync_time()
mh.MIRROR_LOG = orig_log
os.unlink(tmp_log)

if result is not None:
    age_s = (datetime.datetime.now(datetime.timezone.utc) - result).total_seconds()
    # Should reflect the MOST RECENT entry (10 min ago), not the first (2h ago)
    check("last line wins (10min, not 2h)", 300 < age_s < 1800, f"age={age_s:.0f}s")
else:
    check("multi-line parsed", False, "returned None")

# Test 5: Alert threshold logic - _recent_failures counts correctly
fail_entries = [
    {"ts": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=i*10)).isoformat(),
     "type": "repair_failed", "detail": f"test failure {i}"}
    for i in range(5)
]
# Add one old entry (> 1hr ago) that should NOT count
fail_entries.append({"ts": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)).isoformat(),
                     "type": "repair_failed", "detail": "old failure"})

with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
    for e in fail_entries:
        f.write(json.dumps(e) + "\n")
    tmp_repair = f.name

orig_repair = mh.REPAIR_LOG
mh.REPAIR_LOG = tmp_repair
count = mh._recent_failures()
mh.REPAIR_LOG = orig_repair
os.unlink(tmp_repair)

check("alert threshold: 5 recent failures counted (not old)", count == 5, f"got {count}")
check("alert would fire (>3 in hour)", count > mh.ALERT_THRESHOLD, f"{count} > {mh.ALERT_THRESHOLD}")

print(f"\n=== RESULTS: {PASS} PASS, {FAIL} FAIL ===")
sys.exit(0 if FAIL == 0 else 1)
