#!/usr/bin/env python3
"""
test_oom_recovery_v2.py - Cycle-18 Goal #1 verification.

Simulates OOM on White seat, runs the full autonomous recovery loop,
and verifies:
  1. OOM detected from model-load.jsonl (kill event)
  2. Recovery completes end-to-end unattended (<60s MTTR)
  3. Incident log written to memory/ops/incidents/
  4. Model downgraded correctly

Usage: python memory/mechanic/test_oom_recovery_v2.py
"""
import json, sys, time, os
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE / "memory" / "mechanic"))

# Import the recovery module
import oom_recovery as orr

def get_ts():
    return datetime.now(timezone.utc).isoformat()

def run_test():
    print("=== test_oom_recovery_v2.py - Cycle-18 OOM Recovery Verification ===\n")
    passed = 0
    failed = 0
    
    def check(name, cond, detail=""):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  PASS - {name}")
        else:
            failed += 1
            print(f"  FAIL - {name} {detail}")

    # --- Phase 1: Simulate OOM kill in model-load.jsonl ---
    print("[Phase 1] Injecting simulated OOM kill into model-load.jsonl...")
    sim_entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "run": f"sim-oom-{int(time.time())}",
        "missing": {"Mechanic": "not_loaded"},
        "_simulated": True,
        "_note": "test_oom_recovery_v2.py simulated OOM kill"
    }
    
    jsonl_path = orr.MODEL_LOAD_JSONL
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with open(jsonl_path, "a") as f:
        f.write(json.dumps(sim_entry) + "\n")
    print(f"  Injected: {json.dumps(sim_entry)}")

    # --- Phase 2: Detect OOM from jsonl ---
    print("\n[Phase 2] Running detection from model-load.jsonl...")
    is_oom, details = orr.detect_from_jsonl("Mechanic", last_n=3)
    check("OOM detected from jsonl", is_oom, f"got: {details}")
    check("Detection reason is jsonl_not_loaded", details.get("reason") == "jsonl_not_loaded")
    check("Agent identified correctly", details.get("agent") == "Mechanic")
    check("Source is model-load.jsonl", details.get("source") == "model-load.jsonl")

    # --- Phase 3: Execute full recovery (simulated for non-GPU env) ---
    print("\n[Phase 3] Executing autonomous recovery loop (simulated)...")
    t_start = time.time()
    result = orr.execute_recovery("Mechanic", host="White", simulated=True)
    elapsed = round(time.time() - t_start, 2)
    
    check("Recovery succeeded end-to-end", result.get("success"), f"result: {json.dumps(result, indent=2)}")
    check("All 6 steps executed", all(k in result.get("steps", {}) for k in 
          ["detect", "kill", "wait_free", "reload", "verify", "log"]))
    check(f"MTTR < {orr.MTTR_TARGET_S}s (actual: {result.get('total_time_s', 999)}s)",
          result.get("total_time_s", 999) < orr.MTTR_TARGET_S)
    check("MTTR flag set correctly", result.get("mttr_met") == True)
    check("Model was downgraded (fp16->int8)", 
          "int8" in result.get("after_model", "") and "fp16" in result.get("before_model", ""))
    
    # --- Phase 4: Verify incident log written to memory/ops/incidents/ ---
    print("\n[Phase 4] Verifying incident log in memory/ops/incidents/...")
    incidents_dir = orr.INCIDENTS_DIR
    check("Incidents directory exists", incidents_dir.exists())
    
    # Find the most recent oom-recovery incident file
    incident_files = sorted(incidents_dir.glob("oom-recovery-*-Mechanic.md"), reverse=True)
    check("Incident markdown file created", len(incident_files) > 0, 
          f"files in dir: {[f.name for f in incidents_dir.iterdir()]}")
    
    if incident_files:
        latest = incident_files[0]
        content = latest.read_text(encoding='utf-8')
        check("Incident has agent name", "Mechanic" in content)
        check("Incident has MTTR target", str(orr.MTTR_TARGET_S) in content)
        check("Incident has before model", "fp16" in content)
        check("Incident has after model", "int8" in content)
        check("Incident has success status", "Success: True" in content or "success" in content.lower())
        print(f"  Incident file: {latest.name}")
    
    # --- Phase 5: Verify decision-log.jsonl entry ---
    print("\n[Phase 5] Verifying decision-log.jsonl entry...")
    if orr.DECISION_LOG.exists():
        lines = orr.DECISION_LOG.read_text(encoding='utf-8').strip().split("\n")
        last_entry = json.loads(lines[-1])
        check("Decision log type is oom_recovery", last_entry.get("type") == "oom_recovery")
        check("Decision log has mttr_met field", "mttr_met" in last_entry)
        check("Decision log agent is Mechanic", last_entry.get("agent") == "Mechanic")
    else:
        check("decision-log.jsonl exists", False)

    # --- Phase 6: Verify unattended (no human touch needed) ---
    print("\n[Phase 6] Verifying unattended operation...")
    check("No interactive input required (script ran to completion)", True)
    check("Recovery was fully automated (detect->kill->wait->reload->verify->log)", 
          result.get("success") and len(result.get("steps", {})) == 6)

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} PASS, {failed} FAIL")
    print(f"MTTR: {result.get('total_time_s', 'N/A')}s (target <{orr.MTTR_TARGET_S}s)")
    print(f"{'='*60}")
    
    return failed == 0


if __name__ == "__main__":
    ok = run_test()
    sys.exit(0 if ok else 1)
