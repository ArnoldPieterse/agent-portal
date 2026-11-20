#!/usr/bin/env python3
"""mirror_force_sync.py - One-command mirror force-sync (Runbook step D)
Part of Mechanic Goal 10: Runbook Automation (top-5)

Usage: python memory/mechanic/mirror_force_sync.py [--dry-run]

Forces an immediate mirror sync regardless of staleness. Idempotent.
Logs to memory/mechanic/runbook-executions.jsonl. Runtime <60s.
"""
import json, os, subprocess, sys, time, datetime

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # project root
MIRROR_SCRIPT = os.path.join(HERE, "memory_mirror.py")
EXEC_LOG = os.path.join(HERE, "memory", "mechanic", "runbook-executions.jsonl")
TIMEOUT_S = 55  # stay under 60s budget


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def _log_execution(script: str, status: str, detail: str, elapsed_s: float):
    entry = {
        "timestamp": _now().isoformat(),
        "script": script,
        "overall": status,
        "detail": detail,
        "total_seconds": round(elapsed_s, 2),
        "within_budget": elapsed_s < 60,
    }
    os.makedirs(os.path.dirname(EXEC_LOG), exist_ok=True)
    with open(EXEC_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def main():
    dry_run = "--dry-run" in sys.argv
    t0 = time.monotonic()

    # Check mirror script exists
    if not os.path.exists(MIRROR_SCRIPT):
        detail = f"memory_mirror.py not found at {MIRROR_SCRIPT}"
        print(f"FAIL: {detail}")
        if not dry_run:
            _log_execution("mirror_force_sync.py", "FAIL", detail, time.monotonic() - t0)
        return 1

    if dry_run:
        elapsed = time.monotonic() - t0
        print(f"DRY-RUN: would execute {MIRROR_SCRIPT} (timeout={TIMEOUT_S}s)")
        _log_execution("mirror_force_sync.py", "DRY-RUN-PASS", f"script exists, would run {MIRROR_SCRIPT}", elapsed)
        return 0

    # Execute mirror sync
    try:
        result = subprocess.run(
            [sys.executable, MIRROR_SCRIPT],
            capture_output=True, text=True, timeout=TIMEOUT_S,
        )
        elapsed = time.monotonic() - t0
        if result.returncode == 0:
            detail = f"sync OK ({elapsed:.1f}s)"
            print(f"PASS: {detail}")
            _log_execution("mirror_force_sync.py", "PASS", detail, elapsed)
            return 0
        else:
            stderr_tail = (result.stderr or "")[-200:]
            detail = f"sync exited rc={result.returncode}: {stderr_tail}"
            print(f"FAIL: {detail}")
            _log_execution("mirror_force_sync.py", "FAIL", detail, elapsed)
            return 1
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - t0
        detail = f"sync timed out after {TIMEOUT_S}s"
        print(f"FAIL: {detail}")
        _log_execution("mirror_force_sync.py", "FAIL", detail, elapsed)
        return 1
    except Exception as e:
        elapsed = time.monotonic() - t0
        detail = f"unexpected error: {e.__class__.__name__}: {e}"
        print(f"FAIL: {detail}")
        _log_execution("mirror_force_sync.py", "FAIL", detail, elapsed)
        return 1


if __name__ == "__main__":
    sys.exit(main())
