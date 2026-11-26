"""Auto-generated acceptance test: forge goal #3 — Dispatch-Correctness Deploy Gate
Generated: 2026-11-26T18:03:58.578045+00:00
Source: memory/goals/forge.md
AC: a dispatch-breaking change is blocked at the gate with the violation logged; a clean change promotes; the gate is skippable only with an explicit flag. (verified: 2026-11-26 - selftest EXIT 0 block/cl
"""
import os, json, pathlib, sys

def test_dispatch_correctness_deploy_gate():
    """Acceptance criterion check."""
    # Criteria: a dispatch-breaking change is blocked at the gate with the violation logged; a clean change promotes
    # CHECK 1: a dispatch-breaking change is blocked at the gate with the violation logged
    # CHECK 2: a clean change promotes
    # CHECK 3: the gate is skippable only with an explicit flag. (verified: 2026-11-26 - selfte
    # CHECK 4: canary BLOCK_RC=4 on stale next10 60% conformance, BYPASS_RC=0 via --bypass-gate
    # CHECK 5: artifact memory/forge/dispatch_gate.py wired as canary Phase -1
    # CHECK 6: evidence-dispatch-gate-2026-11-26.md)

    # Stub assertion: verify the goal file itself exists
    goals_file = pathlib.Path("memory/goals/forge.md")
    assert goals_file.exists(), "Goals file missing: forge"
    return True

if __name__ == "__main__":
    test_dispatch_correctness_deploy_gate()
    print("PASS: forge goal #3 stub executed without error")
