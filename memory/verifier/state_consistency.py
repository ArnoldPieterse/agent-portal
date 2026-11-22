#!/usr/bin/env python3
"""
state_consistency.py - Fleet State Consistency Check (Verifier goal #5)

Verifies that cockpit state, agents.json, and actual system state (process list,
GPU usage) are mutually consistent.

Detection targets:
  * Agent marked active but no process running
  * Host shown healthy but GPU at 0%
  * Goal count mismatch between cockpit and TODO.md

Acceptance criteria:
  * On consistent system: 0 issues
  * A planted inconsistency is detected within 1 run
  * Check completes <20s
  * Report lists all inconsistencies found

Usage:
  python memory/verifier/state_consistency.py --self-test
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Data source abstractions (pluggable for live vs. simulated)
# ---------------------------------------------------------------------------

class StateSource:
    """Abstract interface for state data sources."""
    def get_cockpit(self):
        raise NotImplementedError

    def get_agents_json(self):
        raise NotImplementedError

    def get_process_list(self):
        raise NotImplementedError

    def get_gpu_usage(self):
        raise NotImplementedError

    def get_goal_counts(self):
        raise NotImplementedError


class SimulatedSource(StateSource):
    """Simulated source for self-test; injectable state."""

    def __init__(self, consistent=True):
        self.consistent = consistent
        # Baseline consistent state
        self._cockpit = {
            "agents": [
                {"name": "verifier", "status": "active", "host": "white", "pid": 1001},
                {"name": "builder", "status": "active", "host": "black", "pid": 2001},
                {"name": "mechanic", "status": "idle", "host": "white", "pid": 3001},
            ],
            "hosts": [
                {"name": "white", "healthy": True, "gpu_pct": 45.0, "cpu_pct": 30.0},
                {"name": "black", "healthy": True, "gpu_pct": 60.0, "cpu_pct": 25.0},
            ],
            "goals_total": 10,
            "goals_completed": 4,
        }
        self._agents_json = {
            "agents": [
                {"name": "verifier", "model_id": "gpt-4o", "status": "active", "host": "white"},
                {"name": "builder", "model_id": "claude-sonnet", "status": "active", "host": "black"},
                {"name": "mechanic", "model_id": "llama-3", "status": "idle", "host": "white"},
            ]
        }
        self._processes = [1001, 2001, 3001]  # running PIDs
        self._gpu = {"white": 45.0, "black": 60.0}
        self._goal_counts = {"total": 10, "completed": 4}

        if not consistent:
            # Plant inconsistencies for negative test
            # 1) Agent 'verifier' marked active but PID 1001 not in process list
            self._processes.remove(1001)
            # 2) Host 'white' shown healthy but GPU at 0%
            self._gpu["white"] = 0.0
            self._cockpit["hosts"][0]["gpu_pct"] = 0.0
            # 3) Goal count mismatch: cockpit says 4 completed, TODO.md says 5
            self._goal_counts["completed"] = 5

    def get_cockpit(self):
        return dict(self._cockpit)

    def get_agents_json(self):
        return dict(self._agents_json)

    def get_process_list(self):
        return list(self._processes)

    def get_gpu_usage(self):
        return dict(self._gpu)

    def get_goal_counts(self):
        return dict(self._goal_counts)


class LiveSource(StateSource):
    """Live source: reads real files and system state."""

    def __init__(self, base_dir="."):
        self.base = Path(base_dir)

    def get_cockpit(self):
        # Try /api/fleet/cockpit; fall back to None if unreachable
        try:
            import urllib.request
            resp = urllib.request.urlopen("http://127.0.0.1:8099/api/fleet/cockpit", timeout=5)
            return json.loads(resp.read())
        except Exception:
            return None

    def get_agents_json(self):
        p = self.base / "agents.json"
        if p.exists():
            with open(p) as f:
                return json.load(f)
        return None

    def get_process_list(self):
        try:
            import subprocess
            out = subprocess.check_output(
                ["tasklist", "/FO", "CSV", "/NH"],
                stderr=subprocess.DEVNULL, timeout=10
            ).decode("utf-8", errors="replace")
            pids = []
            for line in out.strip().splitlines():
                parts = [x.strip('"') for x in line.split(",")]
                if len(parts) >= 2 and parts[1].isdigit():
                    pids.append(int(parts[1]))
            return pids
        except Exception:
            return None

    def get_gpu_usage(self):
        try:
            import subprocess
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                stderr=subprocess.DEVNULL, timeout=10
            ).decode().strip()
            return {f"gpu-{i}": float(x) for i, x in enumerate(out.splitlines())}
        except Exception:
            return None

    def get_goal_counts(self):
        p = self.base / "TODO.md"
        if not p.exists():
            return None
        text = p.read_text(encoding="utf-8", errors="replace")
        total = len(re.findall(r"^\s*\d+\.\s+\*\*", text, re.MULTILINE))
        completed = len(re.findall(r"verified:\s*\d{4}-\d{2}-\d{2}", text))
        return {"total": total, "completed": completed}


# ---------------------------------------------------------------------------
# Consistency checks
# ---------------------------------------------------------------------------

def check_agent_process_consistency(cockpit, process_list):
    """Detect agents marked active but with no running process."""
    issues = []
    if cockpit is None or process_list is None:
        return [{"type": "agent_no_process", "severity": "info",
                 "detail": "Cockpit or process list unavailable - check skipped"}]
    for agent in cockpit.get("agents", []):
        if agent.get("status") == "active":
            pid = agent.get("pid")
            if pid is not None and pid not in process_list:
                issues.append({
                    "type": "agent_no_process",
                    "severity": "error",
                    "agent": agent["name"],
                    "detail": f"Agent '{agent['name']}' marked active (pid={pid}) but no matching process found"
                })
    return issues


def check_host_gpu_consistency(cockpit, gpu_usage):
    """Detect hosts shown healthy but GPU at 0%."""
    issues = []
    if cockpit is None or gpu_usage is None:
        return [{"type": "host_gpu", "severity": "info",
                 "detail": "Cockpit or GPU data unavailable - check skipped"}]
    for host in cockpit.get("hosts", []):
        name = host["name"]
        if host.get("healthy") and gpu_usage.get(name, 0) == 0:
            issues.append({
                "type": "host_gpu_zero",
                "severity": "warning",
                "host": name,
                "detail": f"Host '{name}' shown healthy but GPU usage is 0%"
            })
    return issues


def check_goal_count_consistency(cockpit, goal_counts):
    """Detect goal count mismatch between cockpit and TODO.md."""
    issues = []
    if cockpit is None or goal_counts is None:
        return [{"type": "goal_count", "severity": "info",
                 "detail": "Cockpit or goal counts unavailable - check skipped"}]
    c_total = cockpit.get("goals_total")
    c_completed = cockpit.get("goals_completed")
    t_total = goal_counts.get("total")
    t_completed = goal_counts.get("completed")
    if c_total is not None and t_total is not None and c_total != t_total:
        issues.append({
            "type": "goal_count_mismatch",
            "severity": "error",
            "detail": f"Goal total mismatch: cockpit={c_total}, TODO.md={t_total}"
        })
    if c_completed is not None and t_completed is not None and c_completed != t_completed:
        issues.append({
            "type": "goal_count_mismatch",
            "severity": "error",
            "detail": f"Goal completed mismatch: cockpit={c_completed}, TODO.md={t_completed}"
        })
    return issues


def check_agents_json_vs_cockpit(cockpit, agents_json):
    """Detect status/host mismatches between agents.json and cockpit."""
    issues = []
    if cockpit is None or agents_json is None:
        return [{"type": "agents_json_mismatch", "severity": "info",
                 "detail": "Cockpit or agents.json unavailable - check skipped"}]
    cockpit_agents = {a["name"]: a for a in cockpit.get("agents", [])}
    for aj_agent in agents_json.get("agents", []):
        name = aj_agent["name"]
        if name not in cockpit_agents:
            issues.append({
                "type": "agent_not_in_cockpit",
                "severity": "warning",
                "agent": name,
                "detail": f"Agent '{name}' in agents.json but missing from cockpit"
            })
            continue
        ca = cockpit_agents[name]
        if aj_agent.get("status") != ca.get("status"):
            issues.append({
                "type": "agent_status_mismatch",
                "severity": "warning",
                "agent": name,
                "detail": f"Agent '{name}' status: agents.json={aj_agent.get('status')}, cockpit={ca.get('status')}"
            })
    return issues


# ---------------------------------------------------------------------------
# Main check runner
# ---------------------------------------------------------------------------

def run_consistency_check(source):
    """Run all consistency checks against the given source. Returns report dict."""
    t0 = time.time()

    cockpit = source.get_cockpit()
    agents_json = source.get_agents_json()
    process_list = source.get_process_list()
    gpu_usage = source.get_gpu_usage()
    goal_counts = source.get_goal_counts()

    all_issues = []
    all_issues.extend(check_agent_process_consistency(cockpit, process_list))
    all_issues.extend(check_host_gpu_consistency(cockpit, gpu_usage))
    all_issues.extend(check_goal_count_consistency(cockpit, goal_counts))
    all_issues.extend(check_agents_json_vs_cockpit(cockpit, agents_json))

    elapsed = time.time() - t0

    errors = [i for i in all_issues if i.get("severity") == "error"]
    warnings = [i for i in all_issues if i.get("severity") == "warning"]
    infos = [i for i in all_issues if i.get("severity") == "info"]

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": round(elapsed, 3),
        "total_issues": len(all_issues),
        "errors": len(errors),
        "warnings": len(warnings),
        "infos": len(infos),
        "passed": len(errors) == 0 and len(warnings) == 0,
        "issues": all_issues
    }
    return report


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test():
    print("=" * 64)
    print("state_consistency.py - SELF-TEST")
    print("=" * 64)

    results = []

    # T1: Consistent system -> 0 issues (errors/warnings)
    print("\n[T1] Consistent system...", end=" ")
    src_ok = SimulatedSource(consistent=True)
    r1 = run_consistency_check(src_ok)
    t1_pass = r1["passed"] and r1["errors"] == 0 and r1["warnings"] == 0
    print("PASS" if t1_pass else f"FAIL (errors={r1['errors']}, warnings={r1['warnings']})")
    results.append(("T1_consistent_zero_issues", t1_pass))

    # T2: Planted inconsistency -> detected
    print("[T2] Inconsistent system (planted)...", end=" ")
    src_bad = SimulatedSource(consistent=False)
    r2 = run_consistency_check(src_bad)
    # Expect: agent_no_process + host_gpu_zero + goal_count_mismatch
    types_found = set(i["type"] for i in r2["issues"] if i.get("severity") != "info")
    expected_types = {"agent_no_process", "host_gpu_zero", "goal_count_mismatch"}
    t2_pass = expected_types.issubset(types_found)
    missing = expected_types - types_found
    print("PASS" if t2_pass else f"FAIL (missing: {missing})")
    results.append(("T2_planted_detected", t2_pass))

    # T3: Completes <20s
    print("[T3] Timing (<20s)...", end=" ")
    t3_pass = r1["elapsed_s"] < 20 and r2["elapsed_s"] < 20
    print(f"PASS ({r1['elapsed_s']}s, {r2['elapsed_s']}s)" if t3_pass else f"FAIL ({r1['elapsed_s']}s)")
    results.append(("T3_timing_under_20s", t3_pass))

    # T4: Report structure complete (all required fields present)
    print("[T4] Report structure...", end=" ")
    required_fields = ["timestamp", "elapsed_s", "total_issues", "errors",
                       "warnings", "infos", "passed", "issues"]
    t4_pass = all(f in r1 for f in required_fields) and all(f in r2 for f in required_fields)
    print("PASS" if t4_pass else "FAIL")
    results.append(("T4_report_structure", t4_pass))

    # T5: agents.json vs cockpit cross-check works
    print("[T5] agents.json cross-check...", end=" ")
    src_x = SimulatedSource(consistent=True)
    # Plant a mismatch: change agents_json status for 'verifier'
    src_x._agents_json["agents"][0]["status"] = "idle"
    r5 = run_consistency_check(src_x)
    has_status_mismatch = any(i["type"] == "agent_status_mismatch" for i in r5["issues"])
    t5_pass = has_status_mismatch
    print("PASS" if t5_pass else "FAIL")
    results.append(("T5_agents_json_crosscheck", t5_pass))

    # Summary
    passed = sum(1 for _, p in results if p)
    total = len(results)
    print("\n" + "=" * 64)
    print(f"SUMMARY: {passed}/{total} self-tests passed")

    # Write report
    full_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "self_test_results": [name for name, p in results if p],
        "failed_tests": [name for name, p in results if not p],
        "t1_consistent": r1,
        "t2_inconsistent": r2,
    }
    out_path = "memory/verifier/state_consistency_report.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(full_report, f, indent=2)
    print(f"Report: {out_path}")

    all_pass = passed == total
    print(f"\nSELF-TEST {'PASSED' if all_pass else 'FAILED'} - {passed}/{total} tests green")
    return 0 if all_pass else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fleet State Consistency Check")
    parser.add_argument("--self-test", action="store_true", help="Run self-test with simulated data")
    parser.add_argument("--live", action="store_true", help="Run against live system state")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(self_test())
    elif args.live:
        source = LiveSource()
        report = run_consistency_check(source)
        print(json.dumps(report, indent=2))
        # Write live report
        out_path = "memory/verifier/state_consistency_live.json"
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nLive report: {out_path}")
        sys.exit(0 if report["passed"] else 1)
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
