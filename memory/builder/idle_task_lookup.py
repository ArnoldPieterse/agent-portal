"""idle_task_lookup.py - Role-specific idle task from the maintenance rotation table.

Part of Builder's Goal 1 (Idle Task Injector). Provides:
- ROTATION: structured dict role -> [5 tasks]
- get_idle_task(role, day_of_cycle=None): returns the specific task string for today
- Self-test when run directly: python memory/builder/idle_task_lookup.py

Designed to be imported into agent_portal.py dispatch logic at L4198-4200.
"""
import json
import os
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent  # memory/builder/
OPS_DIR = HERE.parent / "ops"

# Parsed from memory/ops/idle-maintenance-rotation.md (authoritative source)
ROTATION = {
    "Orchestrator": [
        "Roster health audit",
        "Model binding check",
        "Capacity gauge refresh",
        "Dependency graph update",
        "Fleet capacity report",
    ],
    "Researcher": [
        "Re-run stale_claim_scan",
        "Evidence quality trend update",
        "KB index freshness check",
        "Source cross-validation sample",
        "Dictionary gap scan",
    ],
    "Builder": [
        "Orphaned temp file sweep",
        "Build artifact size audit",
        "Pin-file integrity check",
        "CSS token drift scan",
        "Test coverage delta",
    ],
    "Verifier": [
        "Stale test battery re-run",
        "SLO history gap fill",
        "Regression daemon health",
        "Evidence chain audit",
        "Gate log compaction",
    ],
    "Designer": [
        "WCAG contrast spot-check",
        "Breakpoint regression scan",
        "Icon set completeness",
        "Typography scale audit",
        "Animation perf check",
    ],
    "Archivist": [
        "KB coverage re-index",
        "Provenance report refresh",
        "Dangling pointer sweep",
        "Orphan file detection",
        "Index staleness check",
    ],
    "Scribe": [
        "Compression fidelity trend",
        "Handoff log compaction",
        "Decision log summarization",
        "Pattern extraction pass",
        "Cycle narrative draft",
    ],
    "Mechanic": [
        "Host probe battery",
        "Log rotation verify",
        "WinRM leg test",
        "Model lifecycle audit",
        "Capacity plan re-gen",
    ],
}

# Cycle start date (from cycle-15 goals set 2026-11-24)
CYCLE_START = date(2026, 11, 24)


def get_day_of_cycle(today=None):
    """Return (current_date - CYCLE_START).days for rotation index."""
    if today is None:
        today = date.today()
    return (today - CYCLE_START).days


def get_idle_task(role, day_of_cycle=None):
    """Return the specific maintenance task string for a role on the given day.

    Args:
        role: agent name/role key (case-insensitive match)
        day_of_cycle: int or None (auto-compute from CYCLE_START + today)

    Returns:
        str: the task description, or "General maintenance sweep" if role unknown.
    """
    if day_of_cycle is None:
        day_of_cycle = get_day_of_cycle()
    # Case-insensitive role lookup
    role_key = None
    for k in ROTATION:
        if k.lower() == role.lower():
            role_key = k
            break
    if role_key is None:
        return "General maintenance sweep"
    tasks = ROTATION[role_key]
    return tasks[day_of_cycle % len(tasks)]


def get_idle_task_body(role, day_of_cycle=None):
    """Return the full dispatch body text for an idle agent (ready to inject into prompt).

    Replaces the generic 4-option menu at agent_portal.py L4200.
    """
    task = get_idle_task(role, day_of_cycle)
    return (
        "your goals are 100%% reached - execute your assigned maintenance task for today: \"%s\". "
        "Work it to completion with tool calls, record evidence via goal_ledger.py or a note in "
        "memory/ops/maintenance-log.jsonl, then reply [CONCLUDED]. If the task is already done today "
        "(check maintenance-log.jsonl for your name + task), pick ONE of: (a) forecast another agent's "
        "goal into memory/goals/, (b) draft a workflow improvement into memory/ops/, (c) verify and close "
        "one stale evidence claim, (d) do one concrete step on another agent's oldest open goal." % task
    )


def self_test():
    """Run verification checks. Returns (pass_count, fail_count)."""
    passed = failed = 0

    # Test 1: All 8 roles have exactly 5 tasks
    for role in ROTATION:
        if len(ROTATION[role]) == 5:
            passed += 1
        else:
            failed += 1
            print("FAIL: %s has %d tasks (expected 5)" % (role, len(ROTATION[role])))

    # Test 2: No duplicate task IDs within a role
    for role, tasks in ROTATION.items():
        if len(set(t.lower() for t in tasks)) == 5:
            passed += 1
        else:
            failed += 1
            print("FAIL: %s has duplicate tasks" % role)

    # Test 3: Rotation wraps correctly (day 5 = day 0)
    for role in ["Builder", "Verifier"]:
        t0 = get_idle_task(role, day_of_cycle=0)
        t5 = get_idle_task(role, day_of_cycle=5)
        if t0 == t5:
            passed += 1
        else:
            failed += 1
            print("FAIL: %s rotation wrap broken (day0=%r != day5=%r)" % (role, t0, t5))

    # Test 4: Case-insensitive lookup
    t = get_idle_task("builder", day_of_cycle=2)
    if t == ROTATION["Builder"][2]:
        passed += 1
    else:
        failed += 1
        print("FAIL: case-insensitive lookup broken")

    # Test 5: Unknown role returns fallback
    t = get_idle_task("Nonexistent", day_of_cycle=0)
    if t == "General maintenance sweep":
        passed += 1
    else:
        failed += 1
        print("FAIL: unknown role fallback broken")

    # Test 6: Body text contains the specific task
    body = get_idle_task_body("Archivist", day_of_cycle=3)
    if "Orphan file detection" in body:
        passed += 1
    else:
        failed += 1
        print("FAIL: body text missing expected task")

    # Test 7: All tasks across roles are distinct (no cross-role dupes in same column)
    for col in range(5):
        seen = set()
        for role, tasks in ROTATION.items():
            t = tasks[col].lower()
            if t in seen:
                failed += 1
                print("FAIL: duplicate task '%s' at column %d" % (tasks[col], col))
            else:
                seen.add(t)
        passed += 1

    return passed, failed


if __name__ == "__main__":
    p, f = self_test()
    print("\nSelf-test: %d/%d passed" % (p, p + f))
    if f:
        raise SystemExit(1)
    # Show today's assignments as demo
    day = get_day_of_cycle()
    print("\nToday is cycle day %d. Assignments:" % day)
    for role in ROTATION:
        print("  %-14s -> %s" % (role, get_idle_task(role)))
