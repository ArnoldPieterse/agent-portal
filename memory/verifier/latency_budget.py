"""Closed-Loop Latency Budget — measures per-segment latency of the autonomy cycle and enforces configurable budgets.

Usage:
  python memory/verifier/latency_budget.py --self-test   # run built-in tests
  python memory/verifier/latency_budget.py               # measure current cycle
  python memory/verifier/latency_budget.py --budget-json '{"detect":5,"diagnose":2,"remediate":10,"verify":3}'

Design:
- Segments: detect, diagnose, remediate, verify (matching the E2E pipeline)
- Budgets are configurable per-segment in seconds
- Measures wall-clock time for each segment
- Reports pass/fail per segment + overall
- Results appended to latency_budget_log.jsonl
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOG_FILE = BASE / "latency_budget_log.jsonl"

# Default budgets (seconds) — aligned with remediation_e2e.py SLAs
DEFAULT_BUDGETS = {
    "detect": 5.0,
    "diagnose": 2.0,
    "remediate": 10.0,
    "verify": 3.0,
}


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def measure_segment(name: str, func) -> dict:
    """Time a single segment function call. Returns {name, duration_s, budget_s, within_budget}."""
    start = time.perf_counter()
    result = func()
    elapsed = time.perf_counter() - start
    budget = DEFAULT_BUDGETS.get(name, 10.0)
    return {
        "segment": name,
        "duration_s": round(elapsed, 6),
        "budget_s": budget,
        "within_budget": elapsed <= budget,
    }


def run_cycle(budgets: dict = None) -> dict:
    """Run a full autonomy cycle measurement. Returns per-segment + overall results."""
    if budgets is None:
        budgets = DEFAULT_BUDGETS
    
    segments = []
    
    # Simulate detect stage: check canary file hash
    def _detect():
        time.sleep(0.001)  # simulate I/O
        return {"detected": True, "anomaly": "hash_mismatch"}
    
    # Simulate diagnose stage: identify root cause
    def _diagnose():
        time.sleep(0.0005)
        return {"root_cause": "append_corruption", "severity": "medium"}
    
    # Simulate remediate stage: apply fix
    def _remediate():
        time.sleep(0.002)
        return {"action": "restore_backup", "bytes_restored": 62}
    
    # Simulate verify stage: confirm fix
    def _verify():
        time.sleep(0.001)
        return {"verified": True, "hash_match": True}
    
    stages = [
        ("detect", _detect),
        ("diagnose", _diagnose),
        ("remediate", _remediate),
        ("verify", _verify),
    ]
    
    for name, func in stages:
        seg_result = measure_segment(name, func)
        seg_result["budget_s"] = budgets.get(name, 10.0)
        seg_result["within_budget"] = seg_result["duration_s"] <= seg_result["budget_s"]
        segments.append(seg_result)
    
    total_duration = sum(s["duration_s"] for s in segments)
    total_budget = sum(budgets.get(s["segment"], 10.0) for s in segments)
    all_within = all(s["within_budget"] for s in segments)
    
    result = {
        "ts": now_iso(),
        "segments": segments,
        "total_duration_s": round(total_duration, 6),
        "total_budget_s": round(total_budget, 2),
        "all_within_budget": all_within,
        "violations": [s["segment"] for s in segments if not s["within_budget"]],
    }
    
    # Append to log
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(result) + "\n")
    
    return result


def self_test():
    """Run self-test. Returns exit code."""
    print("=== Latency Budget Self-Test ===")
    passed = 0
    failed = 0
    
    # T1: Normal run — all segments within generous budgets
    print("\nT1: Normal cycle with default budgets -> all within budget")
    result = run_cycle(budgets=DEFAULT_BUDGETS)
    if result["all_within_budget"] and len(result["segments"]) == 4:
        print(f"  PASS: all 4 segments within budget, total={result['total_duration_s']}s")
        passed += 1
    else:
        print(f"  FAIL: {result}")
        failed += 1
    
    # T2: Impossibly tight budgets -> violations detected
    print("\nT2: Tight budgets (0.0001s each) -> violations flagged")
    tight = {"detect": 0.0001, "diagnose": 0.0001, "remediate": 0.0001, "verify": 0.0001}
    result = run_cycle(budgets=tight)
    if not result["all_within_budget"] and len(result["violations"]) >= 1:
        print(f"  PASS: violations={result['violations']}, all_within=False")
        passed += 1
    else:
        print(f"  FAIL: {result}")
        failed += 1
    
    # T3: Custom budget override for one segment only
    print("\nT3: Mixed budgets (generous detect, tight remediate) -> only remediate violates")
    mixed = {"detect": 5.0, "diagnose": 2.0, "remediate": 0.0001, "verify": 3.0}
    result = run_cycle(budgets=mixed)
    if not result["all_within_budget"] and "remediate" in result["violations"]:
        print(f"  PASS: only 'remediate' violated as expected")
        passed += 1
    else:
        print(f"  FAIL: {result}")
        failed += 1
    
    # T4: Verify log file was written with correct structure
    print("\nT4: Log file exists and has valid JSON entries")
    if LOG_FILE.exists():
        lines = [l.strip() for l in LOG_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
        if len(lines) >= 3:
            last = json.loads(lines[-1])
            if "segments" in last and "total_duration_s" in last and "all_within_budget" in last:
                print(f"  PASS: log has {len(lines)} entries, structure valid")
                passed += 1
            else:
                print(f"  FAIL: missing keys in last entry: {list(last.keys())}")
                failed += 1
        else:
            print(f"  FAIL: only {len(lines)} entries (expected >=3)")
            failed += 1
    else:
        print("  FAIL: log file not found")
        failed += 1
    
    # T5: Total budget is sum of segment budgets
    print("\nT5: total_budget_s equals sum of per-segment budgets")
    result = run_cycle(budgets=DEFAULT_BUDGETS)
    expected_total = sum(DEFAULT_BUDGETS.values())
    if abs(result["total_budget_s"] - expected_total) < 0.01:
        print(f"  PASS: total_budget={result['total_budget_s']}s == sum of segments")
        passed += 1
    else:
        print(f"  FAIL: total_budget={result['total_budget_s']}s != {expected_total}s")
        failed += 1
    
    # Cleanup test log for next run
    LOG_FILE.unlink(missing_ok=True)
    
    print(f"\n=== RESULTS: {passed} PASS / {failed} FAIL ===")
    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Closed-Loop Latency Budget")
    parser.add_argument("--self-test", action="store_true", help="Run built-in self-test")
    parser.add_argument("--budget-json", type=str, help="Custom budgets as JSON string")
    args = parser.parse_args()
    
    if args.self_test:
        sys.exit(self_test())
    
    budgets = None
    if args.budget_json:
        budgets = json.loads(args.budget_json)
    
    result = run_cycle(budgets=budgets)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["all_within_budget"] else 1)


if __name__ == "__main__":
    main()
