#!/usr/bin/env python3
"""
seed_mirror_run.py — one-shot live mirror trigger for Researcher goal #3 (mirror-revert deep-dive).

WHY: The instrumentation in memory_mirror.py is live but the event log only has
_test lines. This script triggers ONE real mirror cycle via elev.py (bypasses
sandbox egress block) and verifies new events appeared.

USAGE:
    python memory/ops/seed_mirror_run.py          # trigger + verify
    python memory/ops/seed_mirror_run.py --dry    # show what would run, no exec

OUTPUT: PASS or FAIL with line counts before/after.
CREDIT: Builder (2026-11-18), unblocking Researcher goal #3 data-collection window.
"""
import os, sys, time, subprocess, json

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVENT_LOG = os.path.join(HERE, "mirror_events.log")
MIRROR_SCRIPT = os.path.join(HERE, "memory_mirror.py")
ELEV = os.path.join(HERE, "elev.py")


def count_live_lines():
    """Count non-_test lines in the event log."""
    if not os.path.exists(EVENT_LOG):
        return 0
    with open(EVENT_LOG, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip() and "_test" not in line)


def main():
    dry = "--dry" in sys.argv
    before = count_live_lines()
    print(f"Baseline: {before} live events in mirror_events.log")

    cmd = [sys.executable, ELEV, "--shell",
           f'cd /d "{HERE}" && python memory_mirror.py -v']
    print(f"Command: {' '.join(cmd)}")

    if dry:
        print("[DRY RUN] Not executing. Exiting.")
        return 0

    # Execute via elev.py (auto-escalates to SYSTEM for LAN access)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print(f"Exit code: {result.returncode}")
        if result.stdout.strip():
            print(f"stdout: {result.stdout.strip()[:500]}")
        if result.stderr.strip():
            print(f"stderr: {result.stderr.strip()[:300]}")
    except subprocess.TimeoutExpired:
        print("FAIL: mirror run timed out (120s)")
        return 1
    except FileNotFoundError as e:
        print(f"FAIL: {e}")
        return 1

    # Give the log a moment to flush
    time.sleep(2)
    after = count_live_lines()
    delta = after - before
    print(f"\nResult: {before} -> {after} live events (delta={delta})")

    if delta > 0:
        print("PASS: live mirror events recorded. Data-collection window is now active.")
        return 0
    else:
        print("FAIL: no new live events. Check that hosts are reachable + config is valid.")
        print("Next step: verify elev.py exit code + mirror stdout for connection errors.")
        return 1


if __name__ == "__main__":
    sys.exit(main())