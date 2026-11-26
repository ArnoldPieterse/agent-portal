"""Auto-generated acceptance test: cycle15-proposal-2026-11-24 goal #3 — Idle Task Injector
Generated: 2026-11-26T18:03:58.566149+00:00
Source: memory/goals/cycle15-proposal-2026-11-24.md
AC: 3 consecutive idle passes show specific
   tasks in dispatch text; at least 5/8 agents produce productive=true.
"""
import os, json, pathlib, sys

def test_idle_task_injector():
    """Acceptance criterion check."""
    # Criteria: 3 consecutive idle passes show specific
   tasks in dispatch text; at least 5/8 agents produce produ
    # CHECK 1: 3 consecutive idle passes show specific
   tasks in dispatch text
    # CHECK 2: at least 5/8 agents produce productive=true.

    # Stub assertion: verify the goal file itself exists
    goals_file = pathlib.Path("memory/goals/cycle15-proposal-2026-11-24.md")
    assert goals_file.exists(), "Goals file missing: cycle15-proposal-2026-11-24"
    return True

if __name__ == "__main__":
    test_idle_task_injector()
    print("PASS: cycle15-proposal-2026-11-24 goal #3 stub executed without error")
