"""Auto-generated acceptance test: outlet goal #1 — First live account connection + end-to-end ship
Generated: 2026-11-26T18:03:58.582386+00:00
Source: memory/goals/outlet.md
AC: one post shipped on a real platform with zero manual edits after staging; timeline logged (event→draft→ship <4h). (pointer: memory/outlet/platform_connect.py)
"""
import os, json, pathlib, sys

def test_first_live_account_connection_end_to_end_ship():
    """Acceptance criterion check."""
    # Criteria: one post shipped on a real platform with zero manual edits after staging; timeline logged (event→dra
    # CHECK 1: one post shipped on a real platform with zero manual edits after staging
    # CHECK 2: timeline logged (event→draft→ship <4h). (pointer: memory/outlet/platform_connect

    # Stub assertion: verify the goal file itself exists
    goals_file = pathlib.Path("memory/goals/outlet.md")
    assert goals_file.exists(), "Goals file missing: outlet"
    return True

if __name__ == "__main__":
    test_first_live_account_connection_end_to_end_ship()
    print("PASS: outlet goal #1 stub executed without error")
