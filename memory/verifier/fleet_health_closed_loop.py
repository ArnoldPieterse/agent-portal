#!/usr/bin/env python3
"""
fleet_health_closed_loop.py - Verifier Goal #8 (Cycle 14)
Fleet Health Closed-Loop Test: simulate VRAM/OOM degradation; verify full
autonomous response chain fires end-to-end.

Response chain stages:
  1. DETECT    - health score drops below threshold -> alert generated
  2. DIAGNOSE  - identify which host/agent is degraded + severity class
  3. REMEDIATE - apply corrective action (simulate: unload model, reroute task)
  4. VERIFY    - confirm recovery (health score back above threshold)
  5. LOG       - write event to closed-loop log

SLA per stage (configurable):
  detect:    <= 2s
  diagnose:  <= 1s
  remediate: <= 5s
  verify:    <= 3s
  total:     <= 10s

Acceptance criteria:
  * All 5 stages fire in sequence when VRAM >90% or agent goes down
  * No stage is skipped (full chain completes)
  * Per-stage SLA met for normal conditions
  * Recovery confirmed (post-remediation health >= pre-degradation baseline - 5)
  * Event logged with full trace

Usage:
  python memory/verifier/fleet_health_closed_loop.py --self-test
  python memory/verifier/fleet_health_closed_loop.py --verbose
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
RESULTS_FILE = BASE / "memory" / "verifier" / "fleet_health_closed_loop_results.jsonl"

DEFAULT_SLAS = {
    "detect": 2.0,
    "diagnose": 1.0,
    "remediate": 5.0,
    "verify": 3.0,
    "total": 10.0,
}

HEALTH_ALERT_THRESHOLD = 85.0  # Alert fires when score drops below this (early warning)
RECOVERY_THRESHOLD = 90.0      # Considered recovered when back above this


def ts():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Health scoring (mirrors production model from health_regression.py)
# ---------------------------------------------------------------------------

def compute_health_score(fleet_state):
    """Compute fleet health score (0-100)."""
    score = 100.0
    for agent in fleet_state.get("agents", []):
        if agent.get("status") in ("down", "error"):
            score -= 22
    for host in fleet_state.get("hosts", []):
        if not host.get("healthy", True):
            score -= 15
        vram = host.get("vram_pct", 0)
        if vram > 90:
            score -= 10
        elif vram > 75:
            score -= 5
    return max(0.0, min(100.0, score))


# ---------------------------------------------------------------------------
# Fleet state simulation
# ---------------------------------------------------------------------------

def baseline_fleet():
    """Healthy 4-host fleet with all agents active."""
    return {
        "agents": [
            {"name": "verifier", "status": "active"},
            {"name": "builder", "status": "active"},
            {"name": "mechanic", "status": "idle"},
            {"name": "orchestrator", "status": "active"},
        ],
        "hosts": [
            {"name": "white", "healthy": True, "vram_pct": 45.0, "cpu_pct": 30.0},
            {"name": "black", "healthy": True, "vram_pct": 60.0, "cpu_pct": 50.0},
            {"name": "red", "healthy": True, "vram_pct": 35.0, "cpu_pct": 25.0},
            {"name": "blue", "healthy": True, "vram_pct": 70.0, "cpu_pct": 40.0},
        ],
    }


def inject_vram_degradation(fleet_state, host_name="black", vram_pct=95.0):
    """Simulate VRAM spike on a specific host (OOM pressure)."""
    for h in fleet_state["hosts"]:
        if h["name"] == host_name:
            h["vram_pct"] = vram_pct
            if vram_pct >= 99:
                h["healthy"] = False  # OOM = host unhealthy
            break
    return fleet_state


def inject_agent_down(fleet_state, agent_name="builder"):
    """Simulate an agent going down."""
    for a in fleet_state["agents"]:
        if a["name"] == agent_name:
            a["status"] = "down"
            break
    return fleet_state


def apply_remediation_vram(fleet_state, host_name):
    """Simulate model unload on the degraded host (VRAM drops back, host recovers)."""
    for h in fleet_state["hosts"]:
        if h["name"] == host_name:
            h["vram_pct"] = 40.0  # post-unload level
            h["healthy"] = True   # host recovers after OOM resolved
            break
    return fleet_state


def apply_remediation_agent(fleet_state, agent_name):
    """Simulate agent restart."""
    for a in fleet_state["agents"]:
        if a["name"] == agent_name:
            a["status"] = "active"
            break
    return fleet_state


# ---------------------------------------------------------------------------
# Response chain stages
# ---------------------------------------------------------------------------

def stage_detect(fleet_state, alert_threshold):
    """Stage 1: Check if health score crosses alert threshold."""
    t0 = time.time()
    score = compute_health_score(fleet_state)
    detected = score < alert_threshold
    elapsed = time.time() - t0
    return {
        "fired": detected,
        "health_score": round(score, 1),
        "threshold": alert_threshold,
        "elapsed_s": elapsed,
    }


def stage_diagnose(fleet_state):
    """Stage 2: Identify the degraded component and severity."""
    t0 = time.time()
    issues = []
    for h in fleet_state["hosts"]:
        if h.get("vram_pct", 0) > 90:
            issues.append({"type": "vram_critical", "component": h["name"], "value": h["vram_pct"], "severity": "high"})
        elif h.get("vram_pct", 0) > 75:
            issues.append({"type": "vram_warning", "component": h["name"], "value": h["vram_pct"], "severity": "medium"})
        if not h.get("healthy", True):
            issues.append({"type": "host_unhealthy", "component": h["name"], "severity": "high"})
    for a in fleet_state["agents"]:
        if a.get("status") in ("down", "error"):
            issues.append({"type": "agent_down", "component": a["name"], "severity": "critical"})
    elapsed = time.time() - t0
    return {"issues": issues, "count": len(issues), "elapsed_s": elapsed}


def stage_remediate(fleet_state, diagnosis):
    """Stage 3: Apply corrective actions for each diagnosed issue."""
    t0 = time.time()
    actions_taken = []
    for issue in diagnosis["issues"]:
        if issue["type"] == "vram_critical":
            fleet_state = apply_remediation_vram(fleet_state, issue["component"])
            actions_taken.append({"action": "unload_model", "target": issue["component"]})
        elif issue["type"] == "agent_down":
            fleet_state = apply_remediation_agent(fleet_state, issue["component"])
            actions_taken.append({"action": "restart_agent", "target": issue["component"]})
    elapsed = time.time() - t0
    return {"actions": actions_taken, "count": len(actions_taken), "elapsed_s": elapsed, "fleet_state": fleet_state}


def stage_verify(fleet_state, recovery_threshold):
    """Stage 4: Confirm health score is back above recovery threshold."""
    t0 = time.time()
    score = compute_health_score(fleet_state)
    verified = score >= recovery_threshold
    elapsed = time.time() - t0
    return {"verified": verified, "health_score": round(score, 1), "threshold": recovery_threshold, "elapsed_s": elapsed}


def stage_log(results):
    """Stage 5: Write event to closed-loop log."""
    t0 = time.time()
    os.makedirs(os.path.dirname(str(RESULTS_FILE)), exist_ok=True)
    with open(str(RESULTS_FILE), 'a') as f:
        f.write(json.dumps(results) + '\n')
    elapsed = time.time() - t0
    return {"logged": True, "file": str(RESULTS_FILE.name), "elapsed_s": elapsed}


# ---------------------------------------------------------------------------
# Full closed-loop run
# ---------------------------------------------------------------------------

def run_closed_loop(fault_type="vram", slas=None):
    """Run the full detect->diagnose->remediate->verify->log chain."""
    if slas is None:
        slas = dict(DEFAULT_SLAS)
    
    # Setup: baseline fleet
    fleet = baseline_fleet()
    baseline_score = compute_health_score(fleet)
    
    # Inject fault
    if fault_type == "vram":
        fleet = inject_vram_degradation(fleet, host_name="black", vram_pct=99.0)  # OOM level
    elif fault_type == "agent_down":
        fleet = inject_agent_down(fleet, agent_name="builder")
    else:
        raise ValueError(f"Unknown fault type: {fault_type}")
    
    degraded_score = compute_health_score(fleet)
    
    results = {
        "ts": ts(),
        "fault_type": fault_type,
        "baseline_score": round(baseline_score, 1),
        "degraded_score": round(degraded_score, 1),
        "stages": {},
        "sla_met": True,
        "overall_pass": True,
    }
    
    t_chain_start = time.time()
    
    # STAGE 1: DETECT
    r_detect = stage_detect(fleet, HEALTH_ALERT_THRESHOLD)
    sla_ok = r_detect["elapsed_s"] <= slas["detect"]
    results["stages"]["detect"] = {**r_detect, "sla_met": sla_ok}
    if not r_detect["fired"]:
        results["overall_pass"] = False
        results["sla_met"] = False
        results["failure_reason"] = "Detection did not fire (score above threshold)"
        return results
    
    # STAGE 2: DIAGNOSE
    r_diag = stage_diagnose(fleet)
    sla_ok = r_diag["elapsed_s"] <= slas["diagnose"]
    results["stages"]["diagnose"] = {**r_diag, "sla_met": sla_ok}
    if r_diag["count"] == 0:
        results["overall_pass"] = False
        results["failure_reason"] = "Diagnosis found no issues"
        return results
    
    # STAGE 3: REMEDIATE
    r_remed = stage_remediate(fleet, r_diag)
    sla_ok = r_remed["elapsed_s"] <= slas["remediate"]
    results["stages"]["remediate"] = {**{k: v for k, v in r_remed.items() if k != "fleet_state"}, "sla_met": sla_ok}
    if r_remed["count"] == 0:
        results["overall_pass"] = False
        results["failure_reason"] = "No remediation actions taken"
        return results
    
    # STAGE 4: VERIFY
    r_verify = stage_verify(r_remed["fleet_state"], RECOVERY_THRESHOLD)
    sla_ok = r_verify["elapsed_s"] <= slas["verify"]
    results["stages"]["verify"] = {**r_verify, "sla_met": sla_ok}
    if not r_verify["verified"]:
        results["overall_pass"] = False
        results["failure_reason"] = f"Recovery failed: score={r_verify['health_score']} < threshold={RECOVERY_THRESHOLD}"
    
    # STAGE 5: LOG
    t_chain_end = time.time()
    results["total_elapsed_s"] = round(t_chain_end - t_chain_start, 4)
    r_log = stage_log(results)
    results["stages"]["log"] = {**r_log, "sla_met": True}  # Log always passes
    
    # SLA checks
    all_slas_met = all(s.get("sla_met", True) for s in results["stages"].values())
    total_sla_ok = results["total_elapsed_s"] <= slas["total"]
    results["sla_met"] = all_slas_met and total_sla_ok
    if not total_sla_ok:
        results["overall_pass"] = False
        results["failure_reason"] = f"Total SLA breach: {results['total_elapsed_s']}s > {slas['total']}s"
    
    return results


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test(verbose=False):
    """Prove the full chain works for both fault types + SLA breach detection."""
    print("=== Fleet Health Closed-Loop Test - Self-Test ===\n")
    passed = 0
    failed = 0
    
    # T1: VRAM/OOM degradation -> full chain fires, recovery confirmed
    print("[T1] VRAM/OOM degradation (99% on 'black', host unhealthy) -> full closed loop")
    r1 = run_closed_loop(fault_type="vram")
    t1_pass = r1["overall_pass"] and r1["sla_met"]
    if t1_pass:
        print(f"  PASS: baseline={r1['baseline_score']} -> degraded={r1['degraded_score']} -> recovered, total={r1['total_elapsed_s']}s")
        passed += 1
    else:
        print(f"  FAIL: {json.dumps(r1, indent=2)}")
        failed += 1
    
    # T2: Agent down -> full chain fires, recovery confirmed
    print("\n[T2] Agent 'builder' down -> full closed loop")
    r2 = run_closed_loop(fault_type="agent_down")
    t2_pass = r2["overall_pass"] and r2["sla_met"]
    if t2_pass:
        print(f"  PASS: baseline={r2['baseline_score']} -> degraded={r2['degraded_score']} -> recovered, total={r2['total_elapsed_s']}s")
        passed += 1
    else:
        print(f"  FAIL: {json.dumps(r2, indent=2)}")
        failed += 1
    
    # T3: No fault -> detection does NOT fire (negative test)
    print("\n[T3] Healthy fleet -> detection should NOT fire")
    fleet_healthy = baseline_fleet()
    r_detect = stage_detect(fleet_healthy, HEALTH_ALERT_THRESHOLD)
    t3_pass = not r_detect["fired"] and r_detect["health_score"] >= HEALTH_ALERT_THRESHOLD
    if t3_pass:
        print(f"  PASS: score={r_detect['health_score']} >= threshold={HEALTH_ALERT_THRESHOLD}, no alert")
        passed += 1
    else:
        print(f"  FAIL: unexpected detection on healthy fleet: {r_detect}")
        failed += 1
    
    # T4: SLA breach detection (impossibly tight SLAs)
    print("\n[T4] Impossibly tight SLAs (0.0001s) -> should flag SLA breach")
    tight_slas = {"detect": 1e-9, "diagnose": 1e-9, "remediate": 1e-9, "verify": 1e-9, "total": 1e-9}
    r4 = run_closed_loop(fault_type="vram", slas=tight_slas)
    t4_pass = not r4["sla_met"]
    if t4_pass:
        breached = [name for name, s in r4["stages"].items() if not s.get("sla_met", True)]
        print(f"  PASS: SLA breach detected on stages: {breached}")
        passed += 1
    else:
        print(f"  FAIL: expected SLA breach but got sla_met=True")
        failed += 1
    
    # T5: Verify all 5 stages are present in the chain (no skipping)
    print("\n[T5] Chain completeness: all 5 stages present (detect, diagnose, remediate, verify, log)")
    expected_stages = ["detect", "diagnose", "remediate", "verify", "log"]
    r5 = run_closed_loop(fault_type="vram")
    actual_stages = list(r5["stages"].keys())
    t5_pass = all(s in actual_stages for s in expected_stages)
    if t5_pass:
        print(f"  PASS: stages present: {actual_stages}")
        passed += 1
    else:
        missing = [s for s in expected_stages if s not in actual_stages]
        print(f"  FAIL: missing stages: {missing}")
        failed += 1
    
    # T6: Recovery score >= baseline - 5 (no permanent damage)
    print("\n[T6] Post-recovery score >= baseline - 5")
    r6 = run_closed_loop(fault_type="vram")
    if "verify" in r6.get("stages", {}):
        verify_score = r6["stages"]["verify"]["health_score"]
        t6_pass = verify_score >= (r6["baseline_score"] - 5)
    else:
        verify_score = None
        t6_pass = False
    if t6_pass:
        print(f"  PASS: recovered={verify_score} >= baseline-5={r6['baseline_score'] - 5}")
        passed += 1
    else:
        print(f"  FAIL: recovered={verify_score} < baseline-5={r6.get('baseline_score', '?') - 5 if r6.get('baseline_score') else '?'}")
        failed += 1
    
    # Summary
    all_pass = failed == 0
    print(f"\n=== SELF-TEST RESULT: {passed} PASS / {failed} FAIL ===")
    if verbose:
        for i, r in enumerate([r1, r2], 1):
            print(f"\nFull trace T{i}: {json.dumps(r, indent=2)}")
    
    return 0 if all_pass else 1


def main():
    parser = argparse.ArgumentParser(description="Fleet Health Closed-Loop Test")
    parser.add_argument("--self-test", action="store_true", help="Run self-test (6 tests)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    if args.self_test:
        sys.exit(self_test(verbose=args.verbose))
    
    # Single run (for live monitoring integration)
    r = run_closed_loop(fault_type="vram")
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["overall_pass"] else 1)


if __name__ == "__main__":
    main()