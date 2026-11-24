# Convergence Health Path Fix - 2026-11-25

## What broke
`convergence_health.py` had two wrong file paths:
- seat_matrix: pointed to `memory/fleet/seat-matrix.json` (missing) -> actual: `memory/ops/seat-matrix.json`
- cycle_estimator: pointed to `memory/ops/cycle-estimate.json` (missing) -> actual: `memory/ops/cycle-duration-stats.json`

## What fixed it
Corrected both paths in memory/mechanic/convergence_health.py. Re-ran script: all 4 checks PASS.

## Evidence
- Output: memory/ops/convergence-health.json (overall=PASS, generated 2026-11-25T09:04)
- seat_matrix_fresh: PASS (1.0h old)
- autonomy_score_updated: PASS (1.7h old)
- intervention_log_growing: PASS (10 entries)
- cycle_estimator_running: PASS (9.1h old)

## Runbook note
convergence_health.py path fix: seat-matrix lives in ops/ not fleet/, cycle-estimate is actually cycle-duration-stats.json. Fixed 2026-11-25.
