#!/usr/bin/env python3
"""
nonsandbox_closure_runbook.py - Batched non-sandbox closure for all one-shot blocked goals.

Decision: 2026-11-27 hot note "consolidate all open goals into one batched non-sandbox closure runbook."
Round topic: Fleet Autonomy Convergence - reduce human intervention to ZERO by making
a single script run from any eligible seat close every blocked goal in sequence.

Prereqs (checked by the Forge gate first):
  - Edge/Chrome present on standard Windows paths
  - portal :8099 responding
  - websockets importable
  - CDP egress NOT blocked (WinError 10013)

Usage:
  python memory/pixel/nonsandbox_closure_runbook.py          # dry-run: list what would execute
  python memory/pixel/nonsandbox_closure_runbook.py --fire   # execute all eligible unblocks

Exit codes:
  0 = all items executed successfully (or none were pending)
  1 = one or more items failed
  2 = seat ineligible (prereqs not met)

Each item writes its own evidence file + goal_ledger record on success.
Idempotent: re-running after a partial success skips already-closed goals.
"""
import json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # .../AgentPortal
EVIDENCE_DIR = ROOT / "memory/pixel"
GOAL_LEDGER = ROOT / "memory/researcher/goal_ledger.py"
FORGE_GATE = ROOT / "memory/forge/nonsandbox_seat_gate.py"

# --- Items: (id, lane, goal#, description, command, evidence_path) ---
ITEMS = [
    {
        "id": "pixel-6",
        "lane": "pixel",
        "goal": 6,
        "desc": "Live CDP screenshot leg @375/@768 (DOM scrollWidth + widget visibility)",
        "cmd": [sys.executable, str(ROOT / "memory/pixel/cdp_375_dom_check.py")],
        "evidence": EVIDENCE_DIR / "cdp_375_dom_check.report.json",
        "timeout_s": 200,
    },
    {
        "id": "verifier-perf-gate",
        "lane": "verifier",
        "goal": 4,
        "desc": "Performance regression gate: capture baseline + register daily schtask",
        "cmd": [sys.executable, str(ROOT / "memory/verifier/deploy_perf_gate.py")],
        "evidence": ROOT / "memory/verifier" / "perf-baseline.json",
        "timeout_s": 120,
    },
    {
        "id": "builder-pin-apply",
        "lane": "builder",
        "goal": 3,
        "desc": "Build-Verify-Pin: live PIN_FILES edit + git commit on White",
        "cmd": [sys.executable, str(ROOT / "memory/builder/build_verify_pin.py"), "index.html", "--apply"],
        "evidence": ROOT / "memory/builder" / "pin-apply-log.jsonl",
        "timeout_s": 60,
    },
]


def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_gate(fire: bool) -> bool:
    """Run the Forge eligibility gate. Returns True if eligible."""
    print(f"[{ts()}] Running Forge seat-gate...")
    try:
        r = subprocess.run(
            [sys.executable, str(FORGE_GATE)] + (["--fire"] if fire else []),
            capture_output=True, text=True, timeout=30,
        )
        print(f"  gate exit={r.returncode}")
        if r.stdout:
            for line in r.stdout.strip().splitlines()[-5:]:
                print(f"  {line}")
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        print("  gate TIMEOUT (30s) -> INELIGIBLE")
        return False
    except Exception as e:
        print(f"  gate error: {e} -> INELIGIBLE")
        return False


def goal_closed(lane: str, goal: int) -> bool:
    """Check if a goal is already marked reached in its goal file."""
    gf = ROOT / "memory/goals" / f"{lane}.md"
    if not gf.exists():
        return False
    text = gf.read_text(encoding="utf-8")
    # Look for "(verified:" pattern on the line containing this goal number
    import re
    pattern = rf"(?m)^\d*\.\s+.*#{goal}\b.*\(verified:"
    if not pattern:  # fallback: check for "reached" or "verified" near the goal
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if f"#{goal}" in line or (f"{goal}." in line and "verified" in line.lower()):
                return True
    return bool(re.search(pattern, text))


def run_item(item: dict) -> bool:
    """Execute one unblock item. Returns True on success."""
    lid = item["id"]
    print(f"\n[{ts()}] EXECUTING {lid}: {item['desc']}")

    # Skip if already closed
    if goal_closed(item["lane"], item["goal"]):
        print(f"  SKIP: goal #{item['goal']} already marked reached in goals/{item['lane']}.md")
        return True

    try:
        r = subprocess.run(
            item["cmd"],
            capture_output=True, text=True, timeout=item["timeout_s"],
            cwd=str(ROOT),
        )
        ok = (r.returncode == 0)
        status = "PASS" if ok else f"FAIL (exit {r.returncode})"
        print(f"  {status}")
        if r.stdout:
            for line in r.stdout.strip().splitlines()[-3:]:
                print(f"    {line}")
        if not ok and r.stderr:
            for line in r.stderr.strip().splitlines()[-3:]:
                print(f"    [err] {line}")

        if ok:
            # Write evidence
            ev_path = ROOT / "memory/pixel" / f"evidence-{lid}-closure-{ts().replace('T','_').replace(':','').replace('Z','')}.md"
            ev_path.write_text(
                f"# EVIDENCE - {lid} batched closure\n"
                f"Timestamp: {ts()}\n"
                f"Command: {' '.join(item['cmd'])}\n"
                f"Exit code: 0\n"
                f"Report: {item['evidence'].relative_to(ROOT)}\n"
                f"Executed by: nonsandbox_closure_runbook.py (Pixel, batched run)\n",
                encoding="utf-8",
            )
            print(f"  evidence -> {ev_path.relative_to(ROOT)}")

            # Record in goal ledger
            lr = subprocess.run(
                [sys.executable, str(GOAL_LEDGER), "--record", item["lane"], str(item["goal"]),
                 f"--note", f"batched non-sandbox closure: {item['desc']} (runbook)"],
                capture_output=True, text=True, timeout=30, cwd=str(ROOT),
            )
            if lr.returncode == 0:
                print(f"  goal_ledger recorded: {item['lane']} #{item['goal']}")
            else:
                print(f"  WARNING: goal_ledger failed (exit {lr.returncode}): {lr.stderr[:100]}")

        return ok

    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT ({item['timeout_s']}s)")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    fire = "--fire" in sys.argv
    dry_run = not fire

    print("=" * 70)
    print("NON-SANDBOX CLOSURE RUNBOOK - Fleet Autonomy Convergence")
    print(f"Mode: {'DRY-RUN' if dry_run else 'FIRE'} | {ts()}")
    print("=" * 70)

    # List pending items
    pending = []
    for item in ITEMS:
        closed = goal_closed(item["lane"], item["goal"])
        status = "CLOSED (skip)" if closed else "PENDING"
        print(f"  [{status}] {item['id']}: {item['desc']}")
        if not closed:
            pending.append(item)

    if not pending:
        print("\nAll items already closed. Nothing to do.")
        return 0

    if dry_run:
        print(f"\nDRY-RUN: {len(pending)} item(s) would execute. Re-run with --fire to execute.")
        return 0

    # Gate check (only for items that need browser/portal)
    eligible = check_gate(fire)
    if not eligible:
        print("\nSEAT INELIGIBLE - aborting. See Forge gate output above.")
        print("Unblock: run this script from a non-sandbox seat with portal up + browser present.")
        return 2

    # Execute pending items in order
    results = {}
    for item in pending:
        ok = run_item(item)
        results[item["id"]] = "PASS" if ok else "FAIL"

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for lid, status in results.items():
        print(f"  {lid}: {status}")
    failed = [k for k, v in results.items() if v == "FAIL"]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
