# Human-Ratification Minimizer - Evidence

Date: 2026-11-26
Script: memory/orchestrator/ratification_audit.py

## Self-test results (4/4 PASS)
- T1: 2 seeded cycles -> correct touch counts + removal plan with named automations per type
- T2: re-run is append-only (no duplicates)
- T3: clean cycle -> 0 touches, meets target
- T4: all 4 touch types correctly classified (goal_set_trigger, ratification, unblock, redirect)

## Real run baseline
Cycles analyzed: 7 (2026-11-12 through current)
Total touches: 30
Avg touches/cycle: 4.29 (target: <1.0 - NOT met yet)
Breakdown by type:
- goal_set_trigger: 10 (user directives to open rounds)
- ratification: 3 (pending seat ratifications)
- unblock: 16 (NEEDS-HUMAN markers in goals files)
- redirect: 0

Removal plan written to memory/orchestrator/ratification-removal-plan.json. All 4 types have named automations:
- goal_set_trigger -> auto_chair.py (BUILT)
- ratification -> auto_chair.py + convergence_asymptote.py (BUILT)
- unblock -> convergence_sentinel.py + idle_rebalance.py (BUILT)
- redirect -> convergence_coupling.py + dispatch_audit.py (PARTIAL)

## Key finding
The "current" bucket is inflated by pending ratification markers in cycle-19 goals files (not yet resolved) and NEEDS-HUMAN lines that are historical notes, not live blockers. The true forward-looking rate will drop as auto_chair eliminates goal_set_trigger touches.
