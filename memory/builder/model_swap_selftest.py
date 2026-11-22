#!/usr/bin/env python3
"""Self-test for model_swap.py - verifies full 5-step swap flow with mocked APIs."""
import json, sys, os, time, tempfile, shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import io

# Setup temp workspace
tmp = Path(tempfile.mkdtemp(prefix="msw_test_"))
agents_file = tmp / "agents.json"
decision_log = tmp / "memory" / "ops" / "decision-log.jsonl"
decision_log.parent.mkdir(parents=True)

# Create a test agents.json
agents_data = {
    "agents": [
        {"id": "test_agent", "name": "Test Agent", "model_id": "old-model-q4",
         "studio": "http://mock:8888"},
    ]
}
agents_file.write_text(json.dumps(agents_data, indent=2))

# Patch module paths before importing
sys.path.insert(0, str(Path("memory/builder").resolve()))
import model_swap

# Redirect AGENTS_PATH and DECISION_LOG to temp files
model_swap.AGENTS_PATH = agents_file
model_swap.DECISION_LOG = decision_log

results = []

def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    results.append((name, status, detail))
    print(f"  [{status}] {name}" + (f" ({detail})" if detail else ""))

# --- Test 1: Dry-run ---
print("Test 1: Dry-run mode")
with patch.object(model_swap, 'check_vram', return_value=(True, "VRAM OK: 20 GB free")):
    rc = model_swap.run_swap("test_agent", "new-model-q8", "http://mock:8888", dry_run=True)
    check("dry-run returns 0", rc == 0, f"rc={rc}")

# Verify agents.json unchanged after dry-run
agents_after = json.loads(agents_file.read_text())
check("dry-run does not modify agents.json",
      agents_after["agents"][0]["model_id"] == "old-model-q4")

# Verify decision logged for dry-run
lines = decision_log.read_text().strip().splitlines()
last = json.loads(lines[-1])
check("dry-run logged to decision-log", last["type"] == "model_swap_dry_run" and last["ok"])

# --- Test 2: Full swap success path ---
print("\nTest 2: Full swap (mocked API)")
decision_log.write_text("")  # clear for clean test

with patch.object(model_swap, 'check_vram', return_value=(True, "VRAM OK")), \
     patch.object(model_swap, 'get_loaded_model', side_effect=["old-model-q4", "", "new-model-q8"]), \
     patch.object(model_swap, 'unload_model', return_value=True), \
     patch.object(model_swap, 'load_model', return_value=True), \
     patch.object(model_swap, 'ping_agent', return_value=(True, "pong")), \
     patch.object(model_swap, 'update_agents_json', wraps=model_swap.update_agents_json), \
     patch('time.sleep'):
    rc = model_swap.run_swap("test_agent", "new-model-q8", "http://mock:8888", dry_run=False)
    check("full swap returns 0", rc == 0, f"rc={rc}")

# Verify agents.json updated
agents_after = json.loads(agents_file.read_text())
check("agents.json model_id updated",
      agents_after["agents"][0]["model_id"] == "new-model-q8")

# Verify decision logged
lines = decision_log.read_text().strip().splitlines()
swap_entries = [json.loads(l) for l in lines if json.loads(l).get("type") == "model_swap"]
check("swap decision logged with ok=True",
      len(swap_entries) == 1 and swap_entries[0]["ok"], f"entries={len(swap_entries)}")

# --- Test 3: VRAM failure aborts ---
print("\nTest 3: VRAM insufficient -> abort")
decision_log.write_text("")
with patch.object(model_swap, 'check_vram', return_value=(False, "VRAM insufficient: 2 GB")), \
     patch('time.sleep'):
    rc = model_swap.run_swap("test_agent", "another-model", "http://mock:8888", dry_run=False)
    check("vram failure returns 1", rc == 1, f"rc={rc}")

lines = decision_log.read_text().strip().splitlines()
fail_entries = [json.loads(l) for l in lines if json.loads(l).get("ok") == False]
check("failure logged", len(fail_entries) >= 1 and "vram_insufficient" in fail_entries[0].get("detail",{}).get("error",""))

# --- Test 4: Load failure aborts ---
print("\nTest 4: Load failure -> abort")
decision_log.write_text("")
with patch.object(model_swap, 'check_vram', return_value=(True, "VRAM OK")), \
     patch.object(model_swap, 'get_loaded_model', side_effect=["old-model-q4", "", ""]), \
     patch.object(model_swap, 'unload_model', return_value=True), \
     patch.object(model_swap, 'load_model', return_value=False), \
     patch('time.sleep'):
    rc = model_swap.run_swap("test_agent", "bad-model", "http://mock:8888", dry_run=False)
    check("load failure returns 1", rc == 1, f"rc={rc}")

# --- Test 5: Agent not found ---
print("\nTest 5: Unknown agent")
decision_log.write_text("")
with patch('time.sleep'):
    rc = model_swap.run_swap("nonexistent_agent", "some-model", "http://mock:8888", dry_run=False)
    check("unknown agent returns 1", rc == 1, f"rc={rc}")

# --- Summary ---
print(f"\n{'='*50}")
passed = sum(1 for _,s,_ in results if s == "PASS")
total = len(results)
print(f"RESULTS: {passed}/{total} passed")
if passed == total:
    print("ALL TESTS PASS")
else:
    for name, status, detail in results:
        if status == "FAIL":
            print(f"  FAILED: {name} ({detail})")

# Cleanup
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(0 if passed == total else 1)
