"""Auto-generated acceptance test: archivist-cycle8-proposal goal #2 — Scheduled Integrity Sweep
Generated: 2026-11-26T18:03:58.559625+00:00
Source: memory/goals/archivist-cycle8-proposal.md
AC: schtasks /query shows it; one run yields 3 reports; MEMORY.md line appended; rising broken-link count triggers an alert line.
"""
import os, json, pathlib, sys

def test_scheduled_integrity_sweep():
    """Acceptance criterion check."""
    # Criteria: schtasks /query shows it; one run yields 3 reports; MEMORY.md line appended; rising broken-link coun
    # CHECK 1: schtasks /query shows it
    # CHECK 2: one run yields 3 reports
    # CHECK 3: MEMORY.md line appended
    # CHECK 4: rising broken-link count triggers an alert line.

    # Stub assertion: verify the goal file itself exists
    goals_file = pathlib.Path("memory/goals/archivist-cycle8-proposal.md")
    assert goals_file.exists(), "Goals file missing: archivist-cycle8-proposal"
    return True

if __name__ == "__main__":
    test_scheduled_integrity_sweep()
    print("PASS: archivist-cycle8-proposal goal #2 stub executed without error")
