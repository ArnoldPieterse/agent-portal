#!/usr/bin/env python3
"""
rollback_test.py - Remediation Rollback Test (Verifier goal #3)

For each remediation runbook, verify that the rollback sequence successfully
restores pre-action state.  Execution model:
    action -> verify new state -> rollback -> verify original state restored

Acceptance criteria:
  * >=3 runbooks tested
  * Each has a working rollback
  * State after rollback matches pre-action state (no drift)
  * Report includes before/after hashes

Usage:
  python memory/verifier/rollback_test.py --self-test
  python memory/verifier/rollback_test.py --runbook <name>   # test one runbook
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Runbook definitions (simulated state machines)
# ---------------------------------------------------------------------------

class Runbook:
    """A remediation runbook with action + rollback that mutate a state file."""

    def __init__(self, name, description, action_fn, rollback_fn):
        self.name = name
        self.description = description
        self.action_fn = action_fn
        self.rollback_fn = rollback_fn


# --- Runbook 1: restart_service (simulated) ---
def _rb1_action(state_dir):
    """Simulate restarting portal service: write new PID + uptime reset."""
    svc = os.path.join(state_dir, "portal_service.json")
    with open(svc) as f:
        data = json.load(f)
    data["pid"] = 99999
    data["uptime_seconds"] = 0
    data["last_restart"] = datetime.now(timezone.utc).isoformat()
    with open(svc, "w") as f:
        json.dump(data, f)


def _rb1_rollback(state_dir):
    """Restore original PID + uptime."""
    svc = os.path.join(state_dir, "portal_service.json")
    with open(os.path.join(state_dir, "_rb1_backup")) as f:
        backup = json.load(f)
    with open(svc, "w") as f:
        json.dump(backup, f)


# --- Runbook 2: rebind_agent (simulated) ---
def _rb2_action(state_dir):
    """Simulate rebinding agent 'verifier' to a different model."""
    cfg = os.path.join(state_dir, "agents_config.json")
    with open(cfg) as f:
        data = json.load(f)
    for agent in data["agents"]:
        if agent["name"] == "verifier":
            agent["model_id"] = "swapped-model-v2"
            agent["rebound_at"] = datetime.now(timezone.utc).isoformat()
    with open(cfg, "w") as f:
        json.dump(data, f)


def _rb2_rollback(state_dir):
    """Restore original model binding."""
    cfg = os.path.join(state_dir, "agents_config.json")
    with open(os.path.join(state_dir, "_rb2_backup")) as f:
        backup = json.load(f)
    with open(cfg, "w") as f:
        json.dump(backup, f)


# --- Runbook 3: rotate_log (simulated) ---
def _rb3_action(state_dir):
    """Simulate log rotation: truncate active log, create .1 archive."""
    log = os.path.join(state_dir, "portal.log")
    archive = os.path.join(state_dir, "portal.log.1")
    # Move current to archive (overwrite)
    shutil.copy2(log, archive)
    # Truncate active log
    with open(log, "w") as f:
        f.write("")


def _rb3_rollback(state_dir):
    """Restore original log content from backup."""
    log = os.path.join(state_dir, "portal.log")
    with open(os.path.join(state_dir, "_rb3_backup"), "rb") as f:
        data = f.read()
    with open(log, "wb") as f:
        f.write(data)


# --- Runbook 4: clear_cache (simulated) ---
def _rb4_action(state_dir):
    """Simulate clearing cache: remove cache file."""
    cache = os.path.join(state_dir, "cache.json")
    if os.path.exists(cache):
        os.remove(cache)


def _rb4_rollback(state_dir):
    """Restore cache from backup."""
    backup = os.path.join(state_dir, "_rb4_backup")
    cache = os.path.join(state_dir, "cache.json")
    shutil.copy2(backup, cache)


RUNBOOKS = [
    Runbook("restart_service", "Restart portal service (simulated PID+uptime reset)", _rb1_action, _rb1_rollback),
    Runbook("rebind_agent", "Rebind agent model assignment (simulated config swap)", _rb2_action, _rb2_rollback),
    Runbook("rotate_log", "Rotate portal log file (simulated truncate + archive)", _rb3_action, _rb3_rollback),
    Runbook("clear_cache", "Clear cache file (simulated delete + restore)", _rb4_action, _rb4_rollback),
]


# ---------------------------------------------------------------------------
# State setup / teardown
# ---------------------------------------------------------------------------

def make_state_dir():
    """Create a temp state dir with realistic initial files."""
    d = tempfile.mkdtemp(prefix="rollback_test_")
    # portal_service.json
    with open(os.path.join(d, "portal_service.json"), "w") as f:
        json.dump({"pid": 12345, "uptime_seconds": 86400, "last_restart": "2026-11-01T00:00:00Z"}, f)
    # agents_config.json
    with open(os.path.join(d, "agents_config.json"), "w") as f:
        json.dump({"agents": [
            {"name": "verifier", "model_id": "gpt-4o", "tools": ["python"]},
            {"name": "builder", "model_id": "claude-sonnet", "tools": ["python", "terminal"]}
        ]}, f)
    # portal.log
    with open(os.path.join(d, "portal.log"), "w") as f:
        f.write("2026-11-23 10:00:00 INFO Portal started\n" * 50)
    # cache.json
    with open(os.path.join(d, "cache.json"), "w") as f:
        json.dump({"entries": list(range(100))}, f)
    return d


def backup_state(state_dir):
    """Create backups needed for rollback (simulates pre-action snapshot)."""
    # RB1: backup portal_service.json
    shutil.copy2(os.path.join(state_dir, "portal_service.json"), os.path.join(state_dir, "_rb1_backup"))
    # RB2: backup agents_config.json
    shutil.copy2(os.path.join(state_dir, "agents_config.json"), os.path.join(state_dir, "_rb2_backup"))
    # RB3: backup portal.log
    shutil.copy2(os.path.join(state_dir, "portal.log"), os.path.join(state_dir, "_rb3_backup"))
    # RB4: backup cache.json
    shutil.copy2(os.path.join(state_dir, "cache.json"), os.path.join(state_dir, "_rb4_backup"))


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def hash_file(path):
    """SHA-256 of file content."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_state_files(state_dir):
    """Hash all non-backup state files (the 'state' we care about)."""
    state_files = ["portal_service.json", "agents_config.json", "portal.log", "cache.json"]
    hashes = {}
    for sf in state_files:
        p = os.path.join(state_dir, sf)
        if os.path.exists(p):
            hashes[sf] = hash_file(p)
        else:
            hashes[sf] = None  # file absent
    return hashes


# ---------------------------------------------------------------------------
# Core test logic
# ---------------------------------------------------------------------------

def test_runbook(rb, state_dir):
    """Execute the full cycle: snapshot -> action -> verify changed -> rollback -> verify restored."""
    result = {
        "runbook": rb.name,
        "description": rb.description,
        "steps": [],
        "passed": False,
        "before_hash": None,
        "after_action_hash": None,
        "after_rollback_hash": None,
        "error": None
    }

    try:
        # Step 1: snapshot pre-action state
        before = hash_state_files(state_dir)
        result["before_hash"] = before
        result["steps"].append({"step": "snapshot", "detail": "state captured"})

        # Step 2: execute action
        rb.action_fn(state_dir)
        after_action = hash_state_files(state_dir)
        result["after_action_hash"] = after_action
        result["steps"].append({"step": "action", "detail": "action executed"})

        # Verify state actually changed (action had effect)
        if before == after_action:
            result["error"] = "Action did not change any state file"
            result["steps"].append({"step": "verify_changed", "detail": "FAIL - no change detected"})
            return result
        result["steps"].append({"step": "verify_changed", "detail": "state confirmed changed"})

        # Step 3: execute rollback
        rb.rollback_fn(state_dir)
        after_rollback = hash_state_files(state_dir)
        result["after_rollback_hash"] = after_rollback
        result["steps"].append({"step": "rollback", "detail": "rollback executed"})

        # Verify state restored
        if before == after_rollback:
            result["passed"] = True
            result["steps"].append({"step": "verify_restored", "detail": "state matches pre-action (no drift)"})
        else:
            drifted = [k for k in before if before[k] != after_rollback.get(k)]
            result["error"] = "Drift detected in: %s" % ", ".join(drifted)
            result["steps"].append({"step": "verify_restored", "detail": "FAIL - drift in %s" % drifted})

    except Exception as e:
        result["error"] = "%s: %s" % (type(e).__name__, str(e))
        result["steps"].append({"step": "exception", "detail": result["error"]})

    return result


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test():
    print("=" * 64)
    print("rollback_test.py - SELF-TEST")
    print("=" * 64)

    state_dir = make_state_dir()
    backup_state(state_dir)

    all_results = []
    for rb in RUNBOOKS:
        # Fresh state dir per runbook to avoid cross-contamination
        sd = make_state_dir()
        backup_state(sd)
        r = test_runbook(rb, sd)
        all_results.append(r)
        status = "PASS" if r["passed"] else "FAIL"
        print("\n[%s] %s - %s" % (status, rb.name, rb.description))
        for s in r["steps"]:
            print("    %s: %s" % (s["step"], s["detail"]))
        if r["error"]:
            print("    ERROR: %s" % r["error"])
        # Cleanup
        shutil.rmtree(sd, ignore_errors=True)

    shutil.rmtree(state_dir, ignore_errors=True)

    # Summary
    passed = sum(1 for r in all_results if r["passed"])
    total = len(all_results)
    print("\n" + "=" * 64)
    print("SUMMARY: %d/%d runbooks passed rollback verification" % (passed, total))

    # Write JSON report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_runbooks": total,
        "passed": passed,
        "failed": total - passed,
        "results": all_results
    }
    out_path = "memory/verifier/rollback_test_report.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print("Report written to: %s" % out_path)

    # Acceptance criteria check
    ok = True
    if total < 3:
        print("ACCEPTANCE FAIL: need >=3 runbooks, got %d" % total)
        ok = False
    if passed != total:
        failed_names = [r["runbook"] for r in all_results if not r["passed"]]
        print("ACCEPTANCE FAIL: %d runbook(s) with rollback drift: %s" % (len(failed_names), failed_names))
        ok = False
    # Verify hashes present in report
    for r in all_results:
        if not r.get("before_hash") or not r.get("after_rollback_hash"):
            print("ACCEPTANCE FAIL: missing hash data for %s" % r["runbook"])
            ok = False

    print("\nSELF-TEST %s - %d/%d runbooks verified with working rollback, no drift" % (
        "PASSED" if ok else "FAILED", passed, total))
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# Single runbook test
# ---------------------------------------------------------------------------

def test_single(name):
    rb = next((r for r in RUNBOOKS if r.name == name), None)
    if not rb:
        print("Unknown runbook '%s'. Available: %s" % (name, [r.name for r in RUNBOOKS]))
        return 2
    state_dir = make_state_dir()
    backup_state(state_dir)
    r = test_runbook(rb, state_dir)
    shutil.rmtree(state_dir, ignore_errors=True)
    print(json.dumps(r, indent=2))
    return 0 if r["passed"] else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Remediation Rollback Test")
    parser.add_argument("--self-test", action="store_true", help="Run all runbooks through rollback cycle")
    parser.add_argument("--runbook", help="Test a specific runbook by name")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(self_test())
    elif args.runbook:
        sys.exit(test_single(args.runbook))
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
