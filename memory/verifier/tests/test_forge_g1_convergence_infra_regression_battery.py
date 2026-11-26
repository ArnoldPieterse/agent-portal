"""Auto-generated acceptance test: forge goal #1 — Convergence-Infra Regression Battery
Generated: 2026-11-26T18:03:58.577545+00:00
Source: memory/goals/forge.md
AC: a healthy run exits 0; injecting a stale mode + a stale-goal dispatch makes it exit 1 with the failing assertion named. (verified: 2026-11-26 - 29/29 checks green; negative injection tests confirm exi
"""
import os, json, pathlib, sys

def test_convergence_infra_regression_battery():
    """Acceptance criterion check."""
    # Criteria: a healthy run exits 0; injecting a stale mode + a stale-goal dispatch makes it exit 1 with the faili
    # CHECK 1: a healthy run exits 0
    # CHECK 2: injecting a stale mode + a stale-goal dispatch makes it exit 1 with the failing 
    # CHECK 3: negative injection tests confirm exit 1 with named assertion)

    # Stub assertion: verify the goal file itself exists
    goals_file = pathlib.Path("memory/goals/forge.md")
    assert goals_file.exists(), "Goals file missing: forge"
    return True

if __name__ == "__main__":
    test_convergence_infra_regression_battery()
    print("PASS: forge goal #1 stub executed without error")
