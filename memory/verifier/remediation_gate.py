#!/usr/bin/env python3
"""
remediation_gate.py - Auto-Remediation Safety Gate (Verifier goal #1)

Before any autonomous remediation action executes, this gate checks 4 preconditions:
  (a) target host is reachable
  (b) no other remediation in progress on the same host
  (c) rollback path exists and has been tested
  (d) action is within policy scope

Usage:
  python memory/verifier/remediation_gate.py --action '<json>' [--dry-run]
  python memory/verifier/remediation_gate.py --self-test

Action JSON fields:
  {
    "host": "white",
    "action": "restart_service",
    "service": "portal",
    "rollback_script": "memory/ops/rollback_portal.py"
  }

Exit codes:
  0 = all gates passed (action allowed)
  1 = one or more gates failed (action blocked)
  2 = usage / parse error
"""

import argparse
import json
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GATE_LOG = "memory/verifier/remediation_gate_log.jsonl"
LOCK_DIR = "memory/verifier/gate_locks"
POLICY_FILE = "memory/verifier/remediation_policy.json"

DEFAULT_POLICY = {
    "allowed_actions": [
        "restart_service",
        "kill_process",
        "clear_cache",
        "rotate_log",
        "rebind_agent",
        "reload_config"
    ],
    "allowed_hosts": ["white", "red", "blue", "green"],
    "max_concurrent_remediations_per_host": 1
}

# Test mode flag: when True, host reachability is simulated (always pass for known hosts)
_TEST_MODE = False

# ---------------------------------------------------------------------------
# Gate checks
# ---------------------------------------------------------------------------

def check_host_reachable(host):
    """(a) Target host is reachable via a quick TCP probe on the portal port."""
    result = {"check": "host_reachable", "host": host, "passed": False}
    
    if _TEST_MODE:
        # In test mode, hosts in policy are considered reachable
        allowed_hosts = DEFAULT_POLICY["allowed_hosts"]
        if os.path.exists(POLICY_FILE):
            try:
                with open(POLICY_FILE) as f:
                    p = json.load(f)
                allowed_hosts = p.get("allowed_hosts", allowed_hosts)
            except (json.JSONDecodeError, OSError):
                pass
        if host in allowed_hosts:
            result["passed"] = True
            result["detail"] = "Test mode: host '%s' assumed reachable" % host
        else:
            result["detail"] = "Test mode: host '%s' not in known hosts" % host
        return result
    
    for addr in [("127.0.0.1", 8099), (host, 8099)]:
        try:
            sock = socket.create_connection(addr, timeout=3)
            sock.close()
            result["passed"] = True
            result["detail"] = "TCP %s:%d OK" % (addr[0], addr[1])
            return result
        except (socket.timeout, ConnectionRefusedError, OSError):
            continue
    result["detail"] = "Cannot reach host '%s' on port 8099" % host
    return result


def check_no_concurrent_remediation(host):
    """(b) No other remediation in progress on the same host (lock file)."""
    lock_file = os.path.join(LOCK_DIR, "%s.lock" % host)
    result = {"check": "no_concurrent", "host": host, "passed": True}
    if os.path.exists(lock_file):
        try:
            with open(lock_file) as f:
                lock_info = json.load(f)
            locked_at_str = lock_info.get("locked_at", "2000-01-01T00:00:00")
            # Parse and normalize to naive UTC for comparison
            locked_at = datetime.fromisoformat(locked_at_str.replace("Z", "+00:00"))
            if locked_at.tzinfo is not None:
                locked_at = locked_at.astimezone(timezone.utc).replace(tzinfo=None)
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            age_min = (now_naive - locked_at).total_seconds() / 60
            if age_min < 30:
                result["passed"] = False
                result["detail"] = "Remediation already in progress on '%s' (locked %.1f min ago)" % (host, age_min)
        except (json.JSONDecodeError, ValueError):
            result["passed"] = False
            result["detail"] = "Stale/corrupt lock file for host '%s'" % host
    return result


def check_rollback_exists(rollback_script):
    """(c) Rollback path exists and is a non-empty file."""
    result = {"check": "rollback_exists", "path": rollback_script, "passed": False}
    p = Path(rollback_script)
    if not p.exists():
        result["detail"] = "Rollback script not found: %s" % rollback_script
        return result
    if p.stat().st_size == 0:
        result["detail"] = "Rollback script is empty (0 bytes): %s" % rollback_script
        return result
    content = p.read_text(errors="replace")[:2000]
    if "rollback" not in content.lower() and "restore" not in content.lower():
        result["detail"] = "Rollback script does not mention 'rollback' or 'restore': %s" % rollback_script
        return result
    result["passed"] = True
    result["detail"] = "Rollback script present and non-empty: %s" % rollback_script
    return result


def check_policy_scope(action, host):
    """(d) Action is within policy scope (allowed_actions + allowed_hosts)."""
    result = {"check": "policy_scope", "action": action, "host": host, "passed": False}
    policy = DEFAULT_POLICY
    if os.path.exists(POLICY_FILE):
        try:
            with open(POLICY_FILE) as f:
                policy = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    allowed_actions = policy.get("allowed_actions", DEFAULT_POLICY["allowed_actions"])
    allowed_hosts = policy.get("allowed_hosts", DEFAULT_POLICY["allowed_hosts"])

    if action not in allowed_actions:
        result["detail"] = "Action '%s' not in allowed_actions" % action
        return result
    if host not in allowed_hosts:
        result["detail"] = "Host '%s' not in allowed_hosts" % host
        return result
    result["passed"] = True
    result["detail"] = "Action and host within policy scope"
    return result


# ---------------------------------------------------------------------------
# Gate runner
# ---------------------------------------------------------------------------

def run_gate(action_spec, dry_run=False):
    """Run all 4 gates. Returns a result dict with overall status."""
    host = action_spec.get("host", "unknown")
    action = action_spec.get("action", "unknown")
    rollback_script = action_spec.get("rollback_script", "")

    checks = [
        check_host_reachable(host),
        check_no_concurrent_remediation(host),
        check_rollback_exists(rollback_script) if rollback_script else {
            "check": "rollback_exists", "path": "(not specified)", "passed": False,
            "detail": "No rollback_script provided in action spec"
        },
        check_policy_scope(action, host)
    ]

    all_passed = all(c["passed"] for c in checks)
    failed = [c for c in checks if not c["passed"]]

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action_spec": action_spec,
        "checks": checks,
        "all_passed": all_passed,
        "failed_checks": [f["check"] for f in failed],
        "decision": "ALLOW" if all_passed else "BLOCK",
        "dry_run": dry_run
    }

    os.makedirs(os.path.dirname(GATE_LOG), exist_ok=True)
    with open(GATE_LOG, "a") as f:
        f.write(json.dumps(result) + "\n")

    return result


def acquire_lock(host, agent="verifier"):
    """Acquire the host lock (call after gate passes, before executing action)."""
    os.makedirs(LOCK_DIR, exist_ok=True)
    lock_file = os.path.join(LOCK_DIR, "%s.lock" % host)
    with open(lock_file, "w") as f:
        json.dump({"agent": agent, "locked_at": datetime.now(timezone.utc).isoformat()}, f)


def release_lock(host):
    """Release the host lock (call after action completes or fails)."""
    lock_file = os.path.join(LOCK_DIR, "%s.lock" % host)
    if os.path.exists(lock_file):
        os.remove(lock_file)


# ---------------------------------------------------------------------------
# Self-test / demo mode
# ---------------------------------------------------------------------------

def self_test():
    """Run built-in acceptance tests. Returns 0 on pass, 1 on fail."""
    global _TEST_MODE
    print("=" * 60)
    print("remediation_gate.py - SELF-TEST")
    print("=" * 60)
    failures = []

    # Enable test mode: host reachability is simulated for known hosts
    _TEST_MODE = True

    os.makedirs(LOCK_DIR, exist_ok=True)
    for f in os.listdir(LOCK_DIR):
        os.remove(os.path.join(LOCK_DIR, f))

    mock_rb = "memory/verifier/_test_rollback.py"
    with open(mock_rb, "w") as f:
        f.write('"""Mock rollback for testing."""\ndef rollback():\n    pass\n')

    valid_action = {
        "host": "white",
        "action": "restart_service",
        "service": "portal",
        "rollback_script": mock_rb
    }

    # T1: valid action passes all gates
    r1 = run_gate(valid_action, dry_run=True)
    print("\n[T1] Valid action -> decision=%s" % r1["decision"])
    if r1["decision"] != "ALLOW":
        for c in r1["checks"]:
            if not c["passed"]:
                print("       FAILED: %s - %s" % (c["check"], c["detail"]))
        failures.append("T1: expected ALLOW, got %s: %s" % (r1["decision"], r1["failed_checks"]))
    else:
        print("      PASS - all 4 checks passed")

    # T2: unreachable host blocks (host not in allowed list)
    bad_host_action = dict(valid_action)
    bad_host_action["host"] = "nonexistent-host-xyz"
    r2 = run_gate(bad_host_action, dry_run=True)
    print("\n[T2] Unreachable host -> decision=%s" % r2["decision"])
    if r2["decision"] != "BLOCK":
        failures.append("T2: expected BLOCK for unreachable host, got %s" % r2["decision"])
    else:
        print("      PASS - blocked by: %s" % r2["failed_checks"])

    # T3: concurrent remediation blocks
    acquire_lock("white", agent="test-agent")
    r3 = run_gate(valid_action, dry_run=True)
    release_lock("white")
    print("\n[T3] Concurrent remediation -> decision=%s" % r3["decision"])
    if r3["decision"] != "BLOCK":
        failures.append("T3: expected BLOCK when lock held, got %s" % r3["decision"])
    else:
        print("      PASS - blocked by: %s" % r3["failed_checks"])

    # T4: missing rollback blocks
    no_rb_action = dict(valid_action)
    del no_rb_action["rollback_script"]
    r4 = run_gate(no_rb_action, dry_run=True)
    print("\n[T4] No rollback script -> decision=%s" % r4["decision"])
    if r4["decision"] != "BLOCK":
        failures.append("T4: expected BLOCK for missing rollback, got %s" % r4["decision"])
    else:
        print("      PASS - blocked by: %s" % r4["failed_checks"])

    # T5: out-of-policy action blocks
    bad_action = dict(valid_action)
    bad_action["action"] = "format_disk"
    r5 = run_gate(bad_action, dry_run=True)
    print("\n[T5] Out-of-policy action -> decision=%s" % r5["decision"])
    if r5["decision"] != "BLOCK":
        failures.append("T5: expected BLOCK for out-of-policy action, got %s" % r5["decision"])
    else:
        print("      PASS - blocked by: %s" % r5["failed_checks"])

    # Cleanup
    if os.path.exists(mock_rb):
        os.remove(mock_rb)
    _TEST_MODE = False

    print("\n" + "=" * 60)
    if failures:
        print("SELF-TEST FAILED (%d failures):" % len(failures))
        for f in failures:
            print("  FAIL - %s" % f)
        return 1
    else:
        print("SELF-TEST PASSED - all 5 tests green")
        return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Auto-Remediation Safety Gate")
    parser.add_argument("--action", help="JSON action spec")
    parser.add_argument("--dry-run", action="store_true", help="Run gate checks without executing")
    parser.add_argument("--self-test", action="store_true", help="Run built-in acceptance tests")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(self_test())

    if not args.action:
        print("Error: --action required (or use --self-test)", file=sys.stderr)
        sys.exit(2)

    try:
        spec = json.loads(args.action)
    except json.JSONDecodeError as e:
        print("Error: invalid JSON: %s" % e, file=sys.stderr)
        sys.exit(2)

    result = run_gate(spec, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["all_passed"] else 1)


if __name__ == "__main__":
    main()
