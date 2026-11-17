#!/usr/bin/env python3
"""Chaos drill simulation test - validates rotation + recovery timing logic.
No network needed: monkey-patches check_port and time.sleep to simulate scenarios.
Evidence: memory/mechanic/chaos-drill-sim-evidence.jsonl
"""
import json, os, sys, time, importlib.util
from datetime import datetime, timezone

# Load chaos_drill.py as a module
DRILL_PATH = os.path.join(os.path.dirname(__file__), "..", "ops", "chaos_drill.py")
spec = importlib.util.spec_from_file_location("chaos_drill", DRILL_PATH)
drill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drill)

EVIDENCE_PATH = os.path.join(os.path.dirname(__file__), "chaos-drill-sim-evidence.jsonl")
results = []

def record(check, passed, detail):
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "check": check,
        "pass": passed,
        "detail": detail
    }
    results.append(entry)
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {check}: {detail}")

# --- Test 1: Rotation logic (all 4 hosts in order) ---
print("\nTest 1: Rotation logic")
state = {"last_index": -1, "drills_completed": []}
expected_order = ["White", "Pale", "Black", "Red"]
actual_order = []
for i in range(4):
    h = drill.next_host(state)
    actual_order.append(h)

record("rotation-order-4-hosts", actual_order == expected_order,
       f"got {actual_order}, expected {expected_order}")

# Test wrap-around: after Red, should go back to White
h_next = drill.next_host(state)
record("rotation-wraparound", h_next == "White",
       f"after index 3 (Red), next is {h_next}")

# --- Test 2: Recovery timing - fast recovery (5s) ---
print("\nTest 2: Fast recovery (simulated 5s)")
call_count = [0]
def mock_check_port_fast(host_ip):
    call_count[0] += 1
    return call_count[0] >= 3  # port opens on 3rd poll (~4s with 2s sleep)

real_sleep = time.sleep
time.sleep = lambda s: None  # skip actual waiting
drill.check_port = mock_check_port_fast
recovered, elapsed = drill.wait_recovery("1.2.3.4", timeout=60)
time.sleep = real_sleep

record("fast-recovery-detected", recovered == True,
       f"recovered={recovered}, elapsed={elapsed}s (simulated)")
record("fast-recovery-under-60s", elapsed < 60,
       f"elapsed={elapsed}s < 60s threshold")

# --- Test 3: Recovery timing - slow recovery (58s) ---
print("\nTest 3: Slow recovery (simulated ~58s)")
call_count2 = [0]
def mock_check_port_slow(host_ip):
    call_count2[0] += 1
    return call_count2[0] >= 30  # port opens on 30th poll (~58s)

time.sleep = lambda s: None
drill.check_port = mock_check_port_slow
recovered, elapsed = drill.wait_recovery("1.2.3.4", timeout=60)
time.sleep = real_sleep

record("slow-recovery-detected", recovered == True,
       f"recovered={recovered}, elapsed={elapsed}s (simulated)")
record("slow-recovery-under-60s", elapsed < 60,
       f"elapsed={elapsed}s < 60s threshold")

# --- Test 4: No recovery (timeout) ---
print("\nTest 4: No recovery (port never opens)")
def mock_check_port_dead(host_ip):
    return False

time.sleep = lambda s: None
drill.check_port = mock_check_port_dead
recovered, elapsed = drill.wait_recovery("1.2.3.4", timeout=60)
time.sleep = real_sleep

record("no-recovery-detected", recovered == False,
       f"recovered={recovered} (correctly detected as failure)")
record("no-recovery-timed-out", elapsed >= 60,
       f"elapsed={elapsed}s >= 60s timeout")

# --- Test 5: Dry-run mode writes correct log entry ---
print("\nTest 5: Dry-run mode")
import tempfile, shutil
# Use temp state/log to not pollute real files
orig_state_file = drill.STATE_FILE
orig_log_path = drill.LOG_PATH
tmp_dir = tempfile.mkdtemp()
drill.STATE_FILE = os.path.join(tmp_dir, "state.json")
drill.LOG_PATH = os.path.join(tmp_dir, "log.jsonl")

entry = drill.run_drill("White", "10.0.0.2", dry_run=True)
record("dry-run-verdict", entry.get("verdict") == "DRY_RUN_OK",
       f"verdict={entry.get('verdict')}")
record("dry-run-mode-tag", entry.get("mode") == "dry-run",
       f"mode={entry.get('mode')}")

# Verify log was written
with open(drill.LOG_PATH) as f:
    log_lines = [json.loads(l) for l in f if l.strip()]
record("dry-run-log-written", len(log_lines) == 1 and log_lines[0]["verdict"] == "DRY_RUN_OK",
       f"log has {len(log_lines)} entry(ies)")

# Cleanup temp
shutil.rmtree(tmp_dir)
drill.STATE_FILE = orig_state_file
drill.LOG_PATH = orig_log_path

# --- Test 6: State tracking after successful drill ---
print("\nTest 6: State tracking")
tmp_dir2 = tempfile.mkdtemp()
drill.STATE_FILE = os.path.join(tmp_dir2, "state.json")
drill.LOG_PATH = os.path.join(tmp_dir2, "log.jsonl")

# Simulate a successful drill by patching check_port and kill
call_count3 = [0]
def mock_check_port_ok(host_ip):
    call_count3[0] += 1
    return True  # always up

drill.check_port = mock_check_port_ok
drill.kill_portal_on = lambda h, ip: True
time.sleep = lambda s: None
entry2 = drill.run_drill("White", "10.0.0.2", dry_run=False)
time.sleep = real_sleep

record("live-drill-pass-verdict", entry2.get("verdict") == "PASS",
       f"verdict={entry2.get('verdict')}")

# Check state was updated
state_after = json.load(open(drill.STATE_FILE))
record("state-tracks-completed-drill", len(state_after["drills_completed"]) == 1,
       f"drills_completed has {len(state_after['drills_completed'])} entry(ies)")
record("state-host-correct", state_after["drills_completed"][0]["host"] == "White",
       f"host={state_after['drills_completed'][0]['host']}")

shutil.rmtree(tmp_dir2)
drill.STATE_FILE = orig_state_file
drill.LOG_PATH = orig_log_path

# --- Summary + write evidence ---
print(f"\n{'='*50}")
total = len(results)
passed = sum(1 for r in results if r["pass"])
print(f"RESULT: {passed}/{total} checks PASS")
verdict = "PASS" if passed == total else "FAIL"
print(f"VERDICT: {verdict}")

# Write evidence file
os.makedirs(os.path.dirname(EVIDENCE_PATH), exist_ok=True)
with open(EVIDENCE_PATH, "w") as f:
    for r in results:
        f.write(json.dumps(r) + "\n")
    f.write(json.dumps({"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "check": "SUMMARY", "pass": verdict == "PASS",
                        "detail": f"{passed}/{total} checks passed"}) + "\n")
print(f"Evidence written: {os.path.relpath(EVIDENCE_PATH)}")

sys.exit(0 if verdict == "PASS" else 1)
