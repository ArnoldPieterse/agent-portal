#!/usr/bin/env python3
"""
Decision Policy Compliance Audit (Verifier Goal #4)

Scans decision-log.jsonl for all autonomous decisions and verifies each
complies with remediation-policy.json:
  - correct action for the condition
  - preconditions met
  - within authority scope

Usage:
  python memory/verifier/policy_audit.py            # run against real files (if present)
  python memory/verifier/policy_audit.py --selftest # run embedded self-tests
"""
import json, os, sys, tempfile, shutil
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Policy schema (default if remediation-policy.json absent)
# ---------------------------------------------------------------------------
DEFAULT_POLICY = {
    "version": 1,
    "rules": [
        {
            "condition": "service_down",
            "allowed_actions": ["restart_service", "rebind_agent"],
            "preconditions": ["host_reachable", "no_active_remediation"],
            "authority": ["verifier", "mechanic", "orchestrator"]
        },
        {
            "condition": "high_vram",
            "allowed_actions": ["clear_cache", "rebind_agent"],
            "preconditions": ["host_reachable"],
            "authority": ["mechanic", "orchestrator"]
        },
        {
            "condition": "log_overflow",
            "allowed_actions": ["rotate_log", "clear_cache"],
            "preconditions": ["host_reachable", "disk_space_available"],
            "authority": ["mechanic"]
        }
    ],
    "cycle_start": "2026-11-23T00:00:00"
}

# ---------------------------------------------------------------------------
# Core audit logic
# ---------------------------------------------------------------------------
def load_policy(path=None):
    if path and os.path.isfile(path):
        with open(path) as f:
            return json.load(f)
    return DEFAULT_POLICY

def load_decisions(path):
    """Load decision-log.jsonl entries. Returns list of dicts."""
    if not os.path.isfile(path):
        return []
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries

def audit_entry(entry, policy):
    """
    Audit a single decision entry against policy.
    Returns list of violation strings (empty = compliant).
    """
    violations = []
    condition = entry.get("condition", "")
    action    = entry.get("action", "")
    agent     = entry.get("agent", "")
    preconds  = entry.get("preconditions_met", [])

    # Find matching rule
    rule = None
    for r in policy["rules"]:
        if r["condition"] == condition:
            rule = r
            break

    if rule is None:
        violations.append(f"UNKNOWN_CONDITION: '{condition}' has no policy rule")
        return violations

    # Check action allowed for this condition
    if action not in rule["allowed_actions"]:
        violations.append(
            f"ACTION_NOT_ALLOWED: action '{action}' not in allowed set {rule['allowed_actions']} for condition '{condition}'"
        )

    # Check preconditions met
    missing = set(rule["preconditions"]) - set(preconds)
    if missing:
        violations.append(f"PRECONDITIONS_MISSING: {sorted(missing)} not in preconditions_met")

    # Check authority
    if agent not in rule["authority"]:
        violations.append(
            f"AUTHORITY_EXCEEDED: agent '{agent}' not in authority list {rule['authority']} for condition '{condition}'"
        )

    return violations

def run_audit(decision_path, policy_path=None):
    """
    Run full audit. Returns dict with summary + per-entry details.
    """
    policy   = load_policy(policy_path)
    decisions = load_decisions(decision_path)

    cycle_start = datetime.fromisoformat(policy.get("cycle_start", "2000-01-01T00:00:00"))
    in_scope    = []
    for d in decisions:
        ts_raw = d.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_raw)
            if ts >= cycle_start:
                in_scope.append(d)
        except (ValueError, TypeError):
            pass  # skip entries with unparseable timestamps

    results = []
    total_violations = 0
    for d in in_scope:
        v = audit_entry(d, policy)
        total_violations += len(v)
        results.append({"entry": d, "violations": v})

    return {
        "policy_version":   policy.get("version", 0),
        "cycle_start":      policy.get("cycle_start"),
        "total_decisions":  len(decisions),
        "in_scope":         len(in_scope),
        "violation_count":  total_violations,
        "entries":          results
    }

# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def selftest():
    tmp = tempfile.mkdtemp(prefix="pa_selftest_")
    pass_count = 0
    fail_count = 0

    def check(name, cond):
        nonlocal pass_count, fail_count
        status = "PASS" if cond else "FAIL"
        print(f"  [{status}] {name}")
        if cond: pass_count += 1
        else:   fail_count += 1

    try:
        policy_path = os.path.join(tmp, "remediation-policy.json")
        with open(policy_path, "w") as f:
            json.dump(DEFAULT_POLICY, f)

        # --- T1: clean log produces 0 violations ---
        print("\nT1: Clean log -> 0 violations")
        clean_entries = [
            {"timestamp": "2026-11-23T10:00:00", "condition": "service_down",
             "action": "restart_service", "agent": "mechanic",
             "preconditions_met": ["host_reachable", "no_active_remediation"]},
            {"timestamp": "2026-11-23T11:00:00", "condition": "high_vram",
             "action": "clear_cache", "agent": "orchestrator",
             "preconditions_met": ["host_reachable"]}
        ]
        log_path = os.path.join(tmp, "decision-log.jsonl")
        with open(log_path, "w") as f:
            for e in clean_entries:
                f.write(json.dumps(e) + "\n")

        report = run_audit(log_path, policy_path)
        check("violation_count == 0", report["violation_count"] == 0)
        check("in_scope == 2",         report["in_scope"] == 2)

        # --- T2: injected violation is caught ---
        print("\nT2: Injected policy violation is caught")
        bad_entries = clean_entries + [
            {"timestamp": "2026-11-23T12:00:00", "condition": "service_down",
             "action": "rotate_log",  "agent": "scribe",
             "preconditions_met": ["host_reachable"]}
        ]
        log_path2 = os.path.join(tmp, "decision-log-bad.jsonl")
        with open(log_path2, "w") as f:
            for e in bad_entries:
                f.write(json.dumps(e) + "\n")

        report2 = run_audit(log_path2, policy_path)
        check("violation_count > 0",              report2["violation_count"] > 0)
        last = report2["entries"][-1]
        joined = " ".join(last["violations"])
        check("ACTION_NOT_ALLOWED caught",         "ACTION_NOT_ALLOWED" in joined)
        check("AUTHORITY_EXCEEDED caught",         "AUTHORITY_EXCEEDED" in joined)
        check("PRECONDITIONS_MISSING caught",      "PRECONDITIONS_MISSING" in joined)

        # --- T3: audit covers all entries since cycle start ---
        print("\nT3: Cycle-start filter works")
        mixed_entries = [
            {"timestamp": "2026-11-20T10:00:00", "condition": "service_down",
             "action": "restart_service", "agent": "mechanic",
             "preconditions_met": ["host_reachable", "no_active_remediation"]},
            {"timestamp": "2026-11-23T14:00:00", "condition": "high_vram",
             "action": "clear_cache", "agent": "mechanic",
             "preconditions_met": ["host_reachable"]}
        ]
        log_path3 = os.path.join(tmp, "decision-log-mixed.jsonl")
        with open(log_path3, "w") as f:
            for e in mixed_entries:
                f.write(json.dumps(e) + "\n")

        report3 = run_audit(log_path3, policy_path)
        check("total_decisions == 2",   report3["total_decisions"] == 2)
        check("in_scope == 1 (only cycle-10)", report3["in_scope"] == 1)

        # --- T4: report includes violation count + details ---
        print("\nT4: Report structure complete")
        r = report2
        check("has policy_version",    "policy_version" in r)
        check("has cycle_start",       "cycle_start" in r)
        check("has total_decisions",   "total_decisions" in r)
        check("has violation_count",   "violation_count" in r)
        check("entries have violations list", all("violations" in e for e in r["entries"]))

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = pass_count + fail_count
    print(f"\nSelf-test: {pass_count}/{total} passed")
    return fail_count == 0

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    else:
        base = Path(__file__).resolve().parent.parent.parent
        log_path    = base / "decision-log.jsonl"
        policy_path = base / "remediation-policy.json"
        report = run_audit(str(log_path), str(policy_path))
        out = base / "memory" / "verifier" / "policy_audit_report.json"
        with open(out, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Audit complete: {report['violation_count']} violation(s) across {report['in_scope']} in-scope entries.")
        print(f"Report written to: {out}")
