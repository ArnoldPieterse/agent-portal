# Convergence-Plateau Detection Gate (Forge goal #9)

Run: 2026-11-26T23:36:02.134320

## Part A - state classification (real convergence_asymptote)
- T1 plateau series: {'state': 'PLATEAU', 'fit_A': 85.0, 'latest': 84.995, 'pass': True}  -> OK
- T2 climb series: {'state': 'CLIMBING', 'fit_A': 91.71, 'latest': 80.523, 'pass': True}  -> OK
- T3 boundary: {'near_state': 'PLATEAU', 'far_state': 'CLIMBING', 'pass': True}  -> OK

## Part B - frequency-reduction safety invariant
- real open goals extracted: **65** (sample: ['researcher', 'researcher', 'researcher', 'researcher', 'researcher', 'researcher'])
- B.1 safe (fair reduced cadence, budget=32, window=4): starved=[] -> OK
- B.2 unsafe (static top-B, hidden idx=32): starved=[32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64] flagged=True -> OK
- B.3 coupling (climb budget=65 vs plateau budget=32): state_dependent=True -> OK

## Checks
- T1_plateau_converged: PASS
- T2_climb_not_converged: PASS
- T3_boundary_correct: PASS
- B1_real_open_no_starvation: PASS
- B2_hidden_goal_caught: PASS
- B3_state_dependent: PASS

**RESULT: PASS**