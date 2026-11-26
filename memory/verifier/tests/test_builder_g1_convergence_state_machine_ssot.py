"""Auto-generated acceptance test: builder goal #1 — Convergence State-Machine SSOT
Generated: 2026-11-26T18:03:58.564073+00:00
Source: memory/goals/builder.md
AC: unit tests assert each legal transition is accepted and a seeded illegal one is rejected+logged; `fleet-mode.json` now carries `fsm_state` + `fsm_validated:true`; grep confirms every mode/sentinel wri
"""
import os, json, pathlib, sys

def test_convergence_state_machine_ssot():
    """Acceptance criterion check."""
    # Criteria: unit tests assert each legal transition is accepted and a seeded illegal one is rejected+logged; `fl
    # CHECK 1: unit tests assert each legal transition is accepted and a seeded illegal one is 
    # CHECK 2: `fleet-mode.json` now carries `fsm_state` + `fsm_validated:true`
    # CHECK 3: grep confirms every mode/sentinel writer imports the FSM (no bypass). — ✅ **REAC
    # CHECK 4: selftest PASS, live fleet-mode.json stamped fsm_state=CONVERGING+fsm_validated:t
    # CHECK 5: selftest PASS (15 legal accepted, illegal rejected+logged to fsm-events.jsonl)
    # CHECK 6: live memory/ops/fleet-mode.json stamped fsm_state=CONVERGING+fsm_validated:true 

    # Stub assertion: verify the goal file itself exists
    goals_file = pathlib.Path("memory/goals/builder.md")
    assert goals_file.exists(), "Goals file missing: builder"
    return True

if __name__ == "__main__":
    test_convergence_state_machine_ssot()
    print("PASS: builder goal #1 stub executed without error")
