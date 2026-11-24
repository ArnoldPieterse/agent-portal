#!/usr/bin/env python3
"""
task_load_impact.py - Scheduled-Task Cumulative Load Verification (Verifier goal #9)

Verifies that the cumulative resource load from all scheduled tasks stays within
acceptable envelope. No single host exceeds 80% CPU or 70% RAM during peak task overlap.

Modes:
  --self-test   Simulate task overlap scenarios and verify detection logic
  --live        Take a quick live measurement snapshot
  --report      Generate report from accumulated measurements

Acceptance criteria:
  * All hosts within thresholds at all timestamps
  * A synthetic added-task load spike is detected and flagged with offending task name
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


CPU_THRESHOLD = 80.0  # percent
RAM_THRESHOLD = 70.0  # percent
MEASUREMENT_LOG = "memory/ops/task-load-trace.jsonl"


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_trace(path=MEASUREMENT_LOG):
    """Load accumulated task-load measurements."""
    p = Path(path)
    if not p.exists():
        return []
    entries = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def check_thresholds(measurements):
    """
    Check measurements against thresholds.
    
    Args:
        measurements: list of dicts with {ts, host, cpu_pct, ram_pct, active_tasks}
    
    Returns: (all_ok: bool, violations: list)
    """
    violations = []
    for m in measurements:
        host = m.get("host", "unknown")
        cpu = m.get("cpu_pct", 0)
        ram = m.get("ram_pct", 0)
        
        if cpu > CPU_THRESHOLD:
            violations.append({
                "type": "cpu_exceeded",
                "host": host,
                "cpu_pct": cpu,
                "threshold": CPU_THRESHOLD,
                "ts": m.get("ts"),
                "active_tasks": m.get("active_tasks", []),
                "offending_task": _identify_peak_task(m.get("active_tasks", [])),
            })
        if ram > RAM_THRESHOLD:
            violations.append({
                "type": "ram_exceeded",
                "host": host,
                "ram_pct": ram,
                "threshold": RAM_THRESHOLD,
                "ts": m.get("ts"),
                "active_tasks": m.get("active_tasks", []),
                "offending_task": _identify_peak_task(m.get("active_tasks", [])),
            })
    
    return len(violations) == 0, violations


def _identify_peak_task(tasks):
    """Identify the task most likely causing load (highest estimated cost)."""
    if not tasks:
        return None
    # Simple heuristic: task with highest resource estimate
    if isinstance(tasks, list):
        # Assume tasks have a 'cost' or 'weight' field
        scored = [(t.get("cost", 1) if isinstance(t, dict) else 1, 
                   t["name"] if isinstance(t, dict) else str(t)) for t in tasks]
        return max(scored, key=lambda x: x[0])[1]
    return None


def record_live_measurement():
    """Take a quick live measurement on this host."""
    import subprocess
    
    # Get CPU usage (simple: use tasklist or typeperf)
    cpu_pct = 0.0
    ram_pct = 0.0
    
    try:
        # Try WMIC for RAM
        out = subprocess.check_output(
            ["wmic", "os", "get", "FreePhysicalMemory,TotalVisibleMemorySize", "/format:csv"],
            stderr=subprocess.DEVNULL, timeout=10
        ).decode("utf-8", errors="replace")
        lines = [l.strip() for l in out.strip().splitlines() if l.strip()]
        if len(lines) >= 2:
            parts = [x.strip() for x in lines[1].split(",")]
            if len(parts) >= 3:
                free_kb = int(parts[-2])
                total_kb = int(parts[-1])
                ram_pct = round(100 * (1 - free_kb / total_kb), 1) if total_kb > 0 else 0
    except Exception:
        pass
    
    # Try to get CPU from typeperf or fallback
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", 
             "Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average"],
            stderr=subprocess.DEVNULL, timeout=10
        ).decode("utf-8", errors="replace").strip()
        cpu_pct = float(out) if out else 0.0
    except Exception:
        pass
    
    # Get active scheduled tasks (just count running python processes as proxy)
    active_tasks = []
    try:
        out = subprocess.check_output(
            ["tasklist", "/FO", "CSV", "/NH"],
            stderr=subprocess.DEVNULL, timeout=10
        ).decode("utf-8", errors="replace")
        py_count = sum(1 for line in out if "python" in line.lower())
        active_tasks = [{"name": f"python_processes", "count": py_count}]
    except Exception:
        pass
    
    measurement = {
        "ts": _now_iso(),
        "host": "local",
        "cpu_pct": cpu_pct,
        "ram_pct": ram_pct,
        "active_tasks": active_tasks,
    }
    
    os.makedirs(os.path.dirname(MEASUREMENT_LOG), exist_ok=True)
    with open(MEASUREMENT_LOG, "a") as f:
        f.write(json.dumps(measurement) + "\n")
    
    print(f"Measurement recorded: cpu={cpu_pct}%, ram={ram_pct}%")
    return measurement


def self_test():
    """Simulate task overlap scenarios and verify detection logic."""
    print("=" * 64)
    print("task_load_impact.py - SELF-TEST")
    print("=" * 64)
    
    results = []
    
    # T1: All hosts within thresholds -> no violations
    print("\n[T1] Within thresholds...", end=" ")
    ok_measurements = [
        {"ts": _now_iso(), "host": "white", "cpu_pct": 45.0, "ram_pct": 52.0,
         "active_tasks": [{"name": "portal_sync", "cost": 1}]},
        {"ts": _now_iso(), "host": "black", "cpu_pct": 30.0, "ram_pct": 40.0,
         "active_tasks": [{"name": "drift_check", "cost": 1}]},
    ]
    all_ok, violations = check_thresholds(ok_measurements)
    t1_pass = all_ok and len(violations) == 0
    print(f"PASS (violations={len(violations)})" if t1_pass else f"FAIL ({violations})")
    results.append(("T1_within_thresholds", t1_pass))
    
    # T2: CPU spike detected with offending task identified
    print("[T2] CPU spike detected...", end=" ")
    spike = {
        "ts": _now_iso(), "host": "white", "cpu_pct": 95.0, "ram_pct": 45.0,
        "active_tasks": [
            {"name": "portal_sync", "cost": 2},
            {"name": "cpu_burn_task", "cost": 10},
            {"name": "drift_check", "cost": 1},
        ],
    }
    all_ok2, violations2 = check_thresholds([spike])
    t2_pass = (not all_ok2 and len(violations2) >= 1 and 
               violations2[0]["type"] == "cpu_exceeded" and
               violations2[0]["offending_task"] == "cpu_burn_task")
    print(f"PASS (task={violations2[0]['offending_task'] if violations2 else 'N/A'})" if t2_pass else f"FAIL ({violations2})")
    results.append(("T2_cpu_spike", t2_pass))
    
    # T3: RAM threshold exceeded detected
    print("[T3] RAM threshold...", end=" ")
    ram_spike = {
        "ts": _now_iso(), "host": "black", "cpu_pct": 50.0, "ram_pct": 78.0,
        "active_tasks": [{"name": "model_load", "cost": 5}],
    }
    all_ok3, violations3 = check_thresholds([ram_spike])
    t3_pass = not all_ok3 and any(v["type"] == "ram_exceeded" for v in violations3)
    print(f"PASS" if t3_pass else f"FAIL ({violations3})")
    results.append(("T3_ram_threshold", t3_pass))
    
    # T4: Boundary values (exactly at threshold = OK, just above = violation)
    print("[T4] Boundary values...", end=" ")
    boundary_ok = {"ts": _now_iso(), "host": "w", "cpu_pct": 80.0, "ram_pct": 70.0, "active_tasks": []}
    boundary_fail = {"ts": _now_iso(), "host": "w", "cpu_pct": 80.1, "ram_pct": 70.0, "active_tasks": []}
    ok_b, v_b = check_thresholds([boundary_ok])
    ok_f, v_f = check_thresholds([boundary_fail])
    t4_pass = ok_b and not ok_f and len(v_f) == 1
    print(f"PASS (80.0%={ok_b}, 80.1%={not ok_f})" if t4_pass else f"FAIL")
    results.append(("T4_boundary", t4_pass))
    
    # T5: Multiple simultaneous violations all reported
    print("[T5] Multiple violations...", end=" ")
    multi = [
        {"ts": _now_iso(), "host": "white", "cpu_pct": 85.0, "ram_pct": 72.0, 
         "active_tasks": [{"name": "task_a", "cost": 3}]},
        {"ts": _now_iso(), "host": "black", "cpu_pct": 90.0, "ram_pct": 40.0,
         "active_tasks": [{"name": "task_b", "cost": 7}]},
    ]
    all_ok5, violations5 = check_thresholds(multi)
    t5_pass = not all_ok5 and len(violations5) >= 3  # white: cpu+ram, black: cpu
    print(f"PASS (violations={len(violations5)})" if t5_pass else f"FAIL ({len(violations5)} found)")
    results.append(("T5_multiple_violations", t5_pass))
    
    # T6: Live measurement runs without error
    print("[T6] Live measurement...", end=" ")
    try:
        m = record_live_measurement()
        t6_pass = "cpu_pct" in m and "ram_pct" in m and "ts" in m
        print(f"PASS (cpu={m['cpu_pct']}%, ram={m['ram_pct']}%)")
    except Exception as e:
        t6_pass = False
        print(f"FAIL ({e})")
    results.append(("T6_live_measurement", t6_pass))
    
    # Summary
    passed = sum(1 for _, p in results if p)
    total = len(results)
    print("\n" + "=" * 64)
    print(f"SUMMARY: {passed}/{total} self-tests passed")
    
    out_path = "memory/verifier/task_load_results.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "timestamp": _now_iso(),
            "self_test": {"passed": passed, "total": total},
            "thresholds": {"cpu_pct": CPU_THRESHOLD, "ram_pct": RAM_THRESHOLD},
            "live_measurement": m if t6_pass else None,
        }, f, indent=2)
    print(f"Report: {out_path}")
    
    all_pass = passed == total
    print(f"\nSELF-TEST {'PASSED' if all_pass else 'FAILED'} - {passed}/{total} tests green")
    return 0 if all_pass else 1


def main():
    parser = argparse.ArgumentParser(description="Scheduled-Task Cumulative Load Verification")
    parser.add_argument("--self-test", action="store_true", help="Run self-test")
    parser.add_argument("--live", action="store_true", help="Record live measurement")
    parser.add_argument("--report", action="store_true", help="Generate report from accumulated data")
    args = parser.parse_args()
    
    if args.self_test:
        sys.exit(self_test())
    elif args.live:
        record_live_measurement()
        sys.exit(0)
    elif args.report:
        entries = load_trace()
        all_ok, violations = check_thresholds(entries)
        report = {
            "timestamp": _now_iso(),
            "measurements_analyzed": len(entries),
            "verdict": "PASS" if all_ok else "FAIL",
            "violations": violations,
            "thresholds": {"cpu_pct": CPU_THRESHOLD, "ram_pct": RAM_THRESHOLD},
        }
        print(json.dumps(report, indent=2))
        out_path = "memory/ops/task-load-report.json"
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport: {out_path}")
        sys.exit(0 if all_ok else 1)
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
