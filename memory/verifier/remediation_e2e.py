#!/usr/bin/env python3
"""
remediation_e2e.py - Autonomous Remediation E2E (Verifier Cycle-14 Goal #1)

Full closed-loop fault-injection test: detect -> diagnose -> remediate -> verify,
with per-stage SLA enforcement.

Scenarios:
  R1: Corrupted JSON state file on a host
  R2: Agent marked active but process not responding (simulated timeout)
  R3: Stale cockpit data (last_update > threshold)

Each scenario exercises the full pipeline and measures stage latency against
configurable SLAs. Results written to remediation_e2e_results.jsonl.

Usage:
  python memory/verifier/remediation_e2e.py --self-test
  python memory/verifier/remediation_e2e.py --scenario R1
  python memory/verifier/remediation_e2e.py --slas memory/verifier/e2e_sla.json

Exit codes:
  0 = all scenarios pass (all stages within SLA)
  1 = one or more SLA violations or stage failures
  2 = usage error
"""

import argparse
import json
import os
import sys
import tempfile
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path

def _tmpdir():
    d = "_e2e_tmp"
    os.makedirs(d, exist_ok=True)
    return d

# ---------------------------------------------------------------------------
# SLA Configuration (defaults; overridable via --slas file)
# ---------------------------------------------------------------------------

DEFAULT_SLAS = {
    "detect_ms": 5000,      # fault must be detected within 5s of injection
    "diagnose_ms": 3000,    # root cause identified within 3s of detection
    "remediate_ms": 10000,  # remediation action completes within 10s
    "verify_ms": 5000,      # post-remediation verification within 5s
    "total_ms": 30000       # full cycle end-to-end within 30s
}

RESULTS_FILE = "memory/verifier/remediation_e2e_results.jsonl"
SLA_FILE = "memory/verifier/e2e_sla.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()[:16]

def elapsed_ms(start):
    """Return milliseconds since start (time.monotonic)."""
    return int((time.monotonic() - start) * 1000)

# ---------------------------------------------------------------------------
# Stage Implementations
# ---------------------------------------------------------------------------

class StageResult:
    def __init__(self, name, passed, latency_ms, evidence=""):
        self.name = name
        self.passed = passed
        self.latency_ms = latency_ms
        self.evidence = evidence
        self.sla_ms = None  # set after SLA check

    def to_dict(self):
        d = {
            "stage": self.name,
            "passed": self.passed,
            "latency_ms": self.latency_ms,
            "sla_ms": self.sla_ms,
            "within_sla": (self.sla_ms is not None and self.latency_ms <= self.sla_ms),
            "evidence": self.evidence
        }
        return d

# --- DETECT stage ---

def detect_corrupted_json(state_file):
    """Detect that a JSON state file is corrupted (invalid JSON or schema mismatch)."""
    start = time.monotonic()
    try:
        with open(state_file) as f:
            content = f.read()
        data = json.loads(content)
        # Schema check: must have 'status' field
        if "status" not in data:
            return StageResult("detect", True, elapsed_ms(start),
                               f"schema_mismatch: missing 'status' field")
        return StageResult("detect", False, elapsed_ms(start),
                           "no_fault_detected: valid JSON with expected schema")
    except json.JSONDecodeError as e:
        return StageResult("detect", True, elapsed_ms(start),
                           f"json_parse_error: {str(e)[:80]}")
    except FileNotFoundError:
        return StageResult("detect", True, elapsed_ms(start),
                           "file_missing: state file not found")

def detect_agent_timeout(agent_name, timeout_s=1.0):
    """Detect that an agent is unresponsive (simulated by checking a response file)."""
    start = time.monotonic()
    # Simulate: check if agent response file exists and is fresh (< 5s old)
    resp_file = f"_e2e_tmp/agent_{agent_name}_resp.txt"
    if not os.path.exists(resp_file):
        return StageResult("detect", True, elapsed_ms(start),
                           f"agent_unresponsive: {agent_name} no response file")
    mtime = os.path.getmtime(resp_file)
    age_s = time.time() - mtime
    if age_s > timeout_s:
        return StageResult("detect", True, elapsed_ms(start),
                           f"agent_stale: {agent_name} last response {age_s:.1f}s ago")
    return StageResult("detect", False, elapsed_ms(start),
                       f"no_fault: {agent_name} responded {age_s:.1f}s ago")

def detect_stale_cockpit(cockpit_file, max_age_s=300):
    """Detect that cockpit data is stale (last_update older than threshold)."""
    start = time.monotonic()
    try:
        with open(cockpit_file) as f:
            data = json.load(f)
        last_update_str = data.get("last_update", "")
        if not last_update_str:
            return StageResult("detect", True, elapsed_ms(start),
                               "stale: no last_update field")
        from datetime import datetime
        lt = datetime.fromisoformat(last_update_str.replace("Z", "+00:00"))
        age_s = (datetime.now(timezone.utc) - lt).total_seconds()
        if age_s > max_age_s:
            return StageResult("detect", True, elapsed_ms(start),
                               f"stale_data: last_update {age_s:.0f}s ago (> {max_age_s}s)")
        return StageResult("detect", False, elapsed_ms(start),
                           f"no_fault: data is {age_s:.0f}s old")
    except (json.JSONDecodeError, ValueError) as e:
        return StageResult("detect", True, elapsed_ms(start),
                           f"parse_error: {str(e)[:80]}")

# --- DIAGNOSE stage ---

def diagnose_corrupted_json(state_file, original_hash):
    """Diagnose root cause of JSON corruption."""
    start = time.monotonic()
    try:
        with open(state_file) as f:
            content = f.read()
        current_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        # Determine fault type
        if not content.strip():
            cause = "truncated_write"
        elif len(content) < 10:
            cause = "partial_overwrite"
        else:
            try:
                json.loads(content)
                cause = "schema_drift"
            except json.JSONDecodeError:
                cause = "corrupted_json"
        evidence = f"hash_mismatch: expected={original_hash[:8]} actual={current_hash[:8]}, cause={cause}"
        return StageResult("diagnose", True, elapsed_ms(start), evidence)
    except Exception as e:
        return StageResult("diagnose", False, elapsed_ms(start), f"diagnosis_failed: {str(e)[:80]}")

def diagnose_agent_timeout(agent_name):
    """Diagnose why agent is unresponsive."""
    start = time.monotonic()
    # Simulated diagnosis: check if process would be running (simulated by file marker)
    proc_marker = f"_e2e_tmp/agent_{agent_name}_proc.txt"
    if os.path.exists(proc_marker):
        cause = "process_alive_but_hung"
    else:
        cause = "process_dead"
    return StageResult("diagnose", True, elapsed_ms(start),
                       f"root_cause={cause}, agent={agent_name}")

def diagnose_stale_cockpit(cockpit_file):
    """Diagnose why cockpit data is stale."""
    start = time.monotonic()
    try:
        with open(cockpit_file) as f:
            data = json.load(f)
        # Check if the upstream process marker exists
        proc_marker = "_e2e_tmp/cockpit_updater_running.txt"
        if os.path.exists(proc_marker):
            cause = "updater_alive_but_slow"
        else:
            cause = "updater_process_dead"
        return StageResult("diagnose", True, elapsed_ms(start),
                           f"root_cause={cause}")
    except Exception as e:
        return StageResult("diagnose", False, elapsed_ms(start), f"diagnosis_failed: {str(e)[:80]}")

# --- REMEDIATE stage ---

def remediate_corrupted_json(state_file, backup_dir):
    """Remediate corrupted JSON by restoring from backup or writing default state."""
    start = time.monotonic()
    # Check for backup
    basename = os.path.basename(state_file)
    backup_path = os.path.join(backup_dir, f"bak_{basename}")
    
    if os.path.exists(backup_path):
        # Restore from backup
        import shutil
        shutil.copy2(backup_path, state_file)
        action = "restored_from_backup"
    else:
        # Write default recovery state
        default_state = json.dumps({"status": "recovered", "ts": utc_now(), "note": "auto-remediated"})
        with open(state_file, 'w') as f:
            f.write(default_state)
        action = "wrote_default_recovery"
    
    return StageResult("remediate", True, elapsed_ms(start),
                       f"action={action}, file={basename}")

def remediate_agent_timeout(agent_name):
    """Remediate unresponsive agent by simulating restart."""
    start = time.monotonic()
    # Simulate: create a fresh response file (as if agent restarted)
    resp_file = f"_e2e_tmp/agent_{agent_name}_resp.txt"
    with open(resp_file, 'w') as f:
        f.write(utc_now())
    # Remove proc marker to simulate clean restart
    proc_marker = f"_e2e_tmp/agent_{agent_name}_proc.txt"
    if os.path.exists(proc_marker):
        os.remove(proc_marker)
    return StageResult("remediate", True, elapsed_ms(start),
                       f"action=restart_agent, agent={agent_name}")

def remediate_stale_cockpit(cockpit_file):
    """Remediate stale cockpit by refreshing the data."""
    start = time.monotonic()
    # Simulate: write fresh timestamp
    try:
        with open(cockpit_file) as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {}
    data["last_update"] = utc_now()
    data["status"] = "fresh"
    with open(cockpit_file, 'w') as f:
        json.dump(data, f, indent=2)
    return StageResult("remediate", True, elapsed_ms(start),
                       f"action=refresh_cockpit, file={os.path.basename(cockpit_file)}")

# --- VERIFY stage ---

def verify_corrupted_json_fixed(state_file):
    """Verify that the JSON state file is now valid and has expected schema."""
    start = time.monotonic()
    try:
        with open(state_file) as f:
            data = json.load(f)
        if "status" in data:
            return StageResult("verify", True, elapsed_ms(start),
                               f"recovered: status={data['status']}")
        return StageResult("verify", False, elapsed_ms(start),
                           "verify_failed: missing status field after remediation")
    except json.JSONDecodeError as e:
        return StageResult("verify", False, elapsed_ms(start),
                           f"verify_failed: still corrupted: {str(e)[:60]}")

def verify_agent_responsive(agent_name):
    """Verify agent is now responsive."""
    start = time.monotonic()
    resp_file = f"_e2e_tmp/agent_{agent_name}_resp.txt"
    if os.path.exists(resp_file):
        mtime = os.path.getmtime(resp_file)
        age_s = time.time() - mtime
        if age_s < 5:
            return StageResult("verify", True, elapsed_ms(start),
                               f"responsive: {agent_name} responded {age_s:.1f}s ago")
    return StageResult("verify", False, elapsed_ms(start),
                       f"verify_failed: {agent_name} still unresponsive")

def verify_cockpit_fresh(cockpit_file, max_age_s=300):
    """Verify cockpit data is now fresh."""
    start = time.monotonic()
    try:
        with open(cockpit_file) as f:
            data = json.load(f)
        last_update_str = data.get("last_update", "")
        lt = datetime.fromisoformat(last_update_str.replace("Z", "+00:00"))
        age_s = (datetime.now(timezone.utc) - lt).total_seconds()
        if age_s <= max_age_s:
            return StageResult("verify", True, elapsed_ms(start),
                               f"fresh: last_update {age_s:.1f}s ago")
        return StageResult("verify", False, elapsed_ms(start),
                           f"verify_failed: still stale ({age_s:.0f}s)")
    except Exception as e:
        return StageResult("verify", False, elapsed_ms(start),
                           f"verify_failed: {str(e)[:60]}")

# ---------------------------------------------------------------------------
# Scenario Orchestration
# ---------------------------------------------------------------------------

def run_scenario_r1(slas):
    """R1: Corrupted JSON state file."""
    tmpdir = _tmpdir()
    backup_dir = os.path.join(tmpdir, "backups")
    os.makedirs(backup_dir)
    
    state_file = os.path.join(tmpdir, "host_white_state.json")
    
    # Setup: write valid state + backup
    original = json.dumps({"status": "healthy", "host": "white", "ts": utc_now()})
    with open(state_file, 'w') as f:
        f.write(original)
    original_hash = sha256_file(state_file)
    
    # Backup for remediation
    import shutil
    shutil.copy2(state_file, os.path.join(backup_dir, "bak_host_white_state.json"))
    
    # INJECT FAULT: corrupt the file
    with open(state_file, 'w') as f:
        f.write('{"status": "healthy", "host": "whi')  # truncated
    
    results = []
    
    # DETECT
    t_detect_start = time.monotonic()
    det = detect_corrupted_json(state_file)
    det.latency_ms = elapsed_ms(t_detect_start)
    results.append(det)
    
    if not det.passed:
        return {"scenario": "R1", "stages": [r.to_dict() for r in results],
                "total_ms": 0, "passed": False, "note": "fault not detected"}
    
    # DIAGNOSE
    t_diag_start = time.monotonic()
    diag = diagnose_corrupted_json(state_file, original_hash)
    diag.latency_ms = elapsed_ms(t_diag_start)
    results.append(diag)
    
    if not diag.passed:
        return {"scenario": "R1", "stages": [r.to_dict() for r in results],
                "total_ms": 0, "passed": False, "note": "diagnosis failed"}
    
    # REMEDIATE
    t_rem_start = time.monotonic()
    rem = remediate_corrupted_json(state_file, backup_dir)
    rem.latency_ms = elapsed_ms(t_rem_start)
    results.append(rem)
    
    if not rem.passed:
        return {"scenario": "R1", "stages": [r.to_dict() for r in results],
                "total_ms": 0, "passed": False, "note": "remediation failed"}
    
    # VERIFY
    t_ver_start = time.monotonic()
    ver = verify_corrupted_json_fixed(state_file)
    ver.latency_ms = elapsed_ms(t_ver_start)
    results.append(ver)
    
    total_ms = elapsed_ms(t_detect_start)
    
    # Cleanup
    for f in [state_file, backup_file]:
        if os.path.exists(f):
            os.remove(f)
    
    return {"scenario": "R1", "stages": [r.to_dict() for r in results],
            "total_ms": total_ms, "passed": ver.passed,
            "note": f"corrupted JSON restored from backup; original_hash={original_hash}"}

def run_scenario_r2(slas):
    """R2: Agent unresponsive (simulated timeout)."""
    _tmpdir()
    agent_name = "test_agent"
    
    # Setup: remove any stale files
    for f in [f"_e2e_tmp/agent_{agent_name}_resp.txt", f"_e2e_tmp/agent_{agent_name}_proc.txt"]:
        if os.path.exists(f):
            os.remove(f)
    
    # INJECT FAULT: agent has no response file (dead/hung)
    # (absence IS the fault)
    
    results = []
    
    # DETECT
    t_detect_start = time.monotonic()
    det = detect_agent_timeout(agent_name, timeout_s=1.0)
    det.latency_ms = elapsed_ms(t_detect_start)
    results.append(det)
    
    if not det.passed:
        return {"scenario": "R2", "stages": [r.to_dict() for r in results],
                "total_ms": 0, "passed": False, "note": "fault not detected"}
    
    # DIAGNOSE
    t_diag_start = time.monotonic()
    diag = diagnose_agent_timeout(agent_name)
    diag.latency_ms = elapsed_ms(t_diag_start)
    results.append(diag)
    
    if not diag.passed:
        return {"scenario": "R2", "stages": [r.to_dict() for r in results],
                "total_ms": 0, "passed": False, "note": "diagnosis failed"}
    
    # REMEDIATE
    t_rem_start = time.monotonic()
    rem = remediate_agent_timeout(agent_name)
    rem.latency_ms = elapsed_ms(t_rem_start)
    results.append(rem)
    
    if not rem.passed:
        return {"scenario": "R2", "stages": [r.to_dict() for r in results],
                "total_ms": 0, "passed": False, "note": "remediation failed"}
    
    # VERIFY
    t_ver_start = time.monotonic()
    ver = verify_agent_responsive(agent_name)
    ver.latency_ms = elapsed_ms(t_ver_start)
    results.append(ver)
    
    total_ms = elapsed_ms(t_detect_start)
    
    # Cleanup
    for f in [f"_e2e_tmp/agent_{agent_name}_resp.txt", f"_e2e_tmp/agent_{agent_name}_proc.txt"]:
        if os.path.exists(f):
            os.remove(f)
    
    return {"scenario": "R2", "stages": [r.to_dict() for r in results],
            "total_ms": total_ms, "passed": ver.passed,
            "note": f"agent {agent_name} restarted; response confirmed"}

def run_scenario_r3(slas):
    """R3: Stale cockpit data."""
    tmpdir = _tmpdir()
    cockpit_file = os.path.join(tmpdir, "cockpit_data.json")
    
    # Setup: write stale data (last_update 1 hour ago)
    from datetime import timedelta
    stale_ts = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    with open(cockpit_file, 'w') as f:
        json.dump({"last_update": stale_ts, "health_score": 72, "status": "degraded"}, f)
    
    results = []
    
    # DETECT
    t_detect_start = time.monotonic()
    det = detect_stale_cockpit(cockpit_file, max_age_s=300)
    det.latency_ms = elapsed_ms(t_detect_start)
    results.append(det)
    
    if not det.passed:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return {"scenario": "R3", "stages": [r.to_dict() for r in results],
                "total_ms": 0, "passed": False, "note": "fault not detected"}
    
    # DIAGNOSE
    t_diag_start = time.monotonic()
    diag = diagnose_stale_cockpit(cockpit_file)
    diag.latency_ms = elapsed_ms(t_diag_start)
    results.append(diag)
    
    if not diag.passed:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return {"scenario": "R3", "stages": [r.to_dict() for r in results],
                "total_ms": 0, "passed": False, "note": "diagnosis failed"}
    
    # REMEDIATE
    t_rem_start = time.monotonic()
    rem = remediate_stale_cockpit(cockpit_file)
    rem.latency_ms = elapsed_ms(t_rem_start)
    results.append(rem)
    
    if not rem.passed:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return {"scenario": "R3", "stages": [r.to_dict() for r in results],
                "total_ms": 0, "passed": False, "note": "remediation failed"}
    
    # VERIFY
    t_ver_start = time.monotonic()
    ver = verify_cockpit_fresh(cockpit_file, max_age_s=300)
    ver.latency_ms = elapsed_ms(t_ver_start)
    results.append(ver)
    
    total_ms = elapsed_ms(t_detect_start)
    
    # Cleanup
    shutil.rmtree(tmpdir, ignore_errors=True)
    
    return {"scenario": "R3", "stages": [r.to_dict() for r in results],
            "total_ms": total_ms, "passed": ver.passed,
            "note": f"cockpit data refreshed; updater_process_dead was root cause"}

# ---------------------------------------------------------------------------
# SLA Enforcement
# ---------------------------------------------------------------------------

def apply_slas(result, slas):
    """Apply SLA thresholds to each stage in the result and check compliance."""
    stage_sla_map = {
        "detect": slas["detect_ms"],
        "diagnose": slas["diagnose_ms"],
        "remediate": slas["remediate_ms"],
        "verify": slas["verify_ms"]
    }
    all_within = True
    for stage in result["stages"]:
        sla = stage_sla_map.get(stage["stage"])
        if sla is not None:
            stage["sla_ms"] = sla
            stage["within_sla"] = stage["latency_ms"] <= sla
            if not stage["within_sla"]:
                all_within = False
    
    result["total_sla_ms"] = slas["total_ms"]
    result["total_within_sla"] = result["total_ms"] <= slas["total_ms"]
    if not result["total_within_sla"]:
        all_within = False
    
    result["sla_compliant"] = all_within and result["passed"]
    return result

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_slas(slas_path=None):
    """Load SLA config from file or use defaults."""
    if slas_path and os.path.exists(slas_path):
        with open(slas_path) as f:
            return json.load(f)
    if os.path.exists(SLA_FILE):
        with open(SLA_FILE) as f:
            return json.load(f)
    return DEFAULT_SLAS.copy()

def run_all_scenarios(slas, only=None):
    """Run all scenarios (or a single one if specified)."""
    scenarios = {
        "R1": run_scenario_r1,
        "R2": run_scenario_r2,
        "R3": run_scenario_r3
    }
    
    results = []
    for name in sorted(scenarios.keys()):
        if only and name != only:
            continue
        print(f"  Running {name}...", end=" ")
        result = scenarios[name](slas)
        result = apply_slas(result, slas)
        results.append(result)
        status = "PASS" if result["sla_compliant"] else "FAIL"
        sla_note = "" if result["sla_compliant"] else " [SLA BREACH]"
        print(f"{status} ({result['total_ms']}ms){sla_note}")
    
    return results

def write_results(results):
    """Append results to the JSONL log."""
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    with open(RESULTS_FILE, 'a') as f:
        for r in results:
            entry = {"ts": utc_now(), **r}
            f.write(json.dumps(entry) + '\n')

def self_test():
    """Run full self-test: all scenarios must pass with SLA compliance."""
    print("remediation_e2e.py --self-test")
    print("=" * 60)
    
    slas = load_slas()
    print(f"SLAs: detect<={slas['detect_ms']}ms, diagnose<={slas['diagnose_ms']}ms, "
          f"remediate<={slas['remediate_ms']}ms, verify<={slas['verify_ms']}ms, "
          f"total<={slas['total_ms']}ms")
    print()
    
    results = run_all_scenarios(slas)
    write_results(results)
    
    # Summary
    passed = sum(1 for r in results if r["sla_compliant"])
    total = len(results)
    print()
    print("-" * 60)
    print(f"RESULT: {passed}/{total} scenarios passed (SLA-compliant)")
    
    # Detailed stage breakdown
    for r in results:
        if not r["sla_compliant"]:
            print(f"  FAIL {r['scenario']}: {r.get('note', '')}")
            for s in r["stages"]:
                flag = "OK" if s.get("within_sla") else "BREACH"
                print(f"    {s['stage']:10s} {s['latency_ms']:6d}ms (SLA {s.get('sla_ms', '?')}ms) [{flag}]")
    
    # Negative test: verify that a non-fault state does NOT trigger remediation
    print()
    print("Negative test: valid state should NOT trigger detection...")
    tmpdir = _tmpdir()
    state_file = os.path.join(tmpdir, "valid_state.json")
    with open(state_file, 'w') as f:
        json.dump({"status": "healthy", "host": "white"}, f)
    
    det = detect_corrupted_json(state_file)
    neg_pass = not det.passed  # detection should NOT fire on valid state
    print(f"  [{'PASS' if neg_pass else 'FAIL'}] Valid state correctly NOT flagged")
    
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    
    all_pass = (passed == total) and neg_pass
    print()
    print(f"OVERALL: {'ALL GREEN' if all_pass else 'FAILURE DETECTED'}")
    return 0 if all_pass else 1

def main():
    parser = argparse.ArgumentParser(description="Autonomous Remediation E2E Test")
    parser.add_argument("--self-test", action="store_true", help="Run full self-test")
    parser.add_argument("--scenario", choices=["R1", "R2", "R3"], help="Run single scenario")
    parser.add_argument("--slas", type=str, default=None, help="Path to SLA config JSON")
    args = parser.parse_args()
    
    if args.self_test:
        sys.exit(self_test())
    elif args.scenario:
        slas = load_slas(args.slas)
        results = run_all_scenarios(slas, only=args.scenario)
        write_results(results)
        for r in results:
            print(json.dumps(r, indent=2))
        sys.exit(0 if all(r["sla_compliant"] for r in results) else 1)
    else:
        # Default: run self-test
        sys.exit(self_test())

if __name__ == "__main__":
    main()
