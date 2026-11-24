# Evidence: Autonomy Score Confidence Interval (Goal #10)
Date: 2026-11-25T17:05Z
Command: `python memory/builder/convergence_health.py --selftest`
Result: 14/14 PASS

## What was implemented
- `compute_confidence_interval(scores)`: t-approximation with n-dependent t-values (4.30 for n<5, 2.78 for 5<=n<10, 2.26 for 10<=n<30, 1.96 for n>=30)
- `validate_autonomy_score_field(value)`: backward-compatible schema validator (accepts old scalar + new object format)
- `write_autonomy_score_to_fleet_mode(result, ci_data)`: atomic write of {score, ci_lower, ci_upper, n_samples} to fleet-mode.json
- Wired into `run()` path so production runs update fleet-mode.json automatically

## Selftest coverage (14 tests)
1. IDLE mode -> 1.0
2. WORK + no productive -> low
3. All productive -> 1.0
4. Half productive -> 0.5
5. No data -> neutral 0.5
6. goal_velocity valid range
7. Full pipeline valid output
8. Atomic write works
9. MAINTENANCE mode -> 1.0
10. CI narrows as n increases (n=5 vs n=30)
11. CI widens when variance increases (tight vs wide spread)
12. Schema validator accepts old scalar format (0, 50, 100 valid; -5, 105 invalid)
13. Schema validator accepts new object format (full + minimal)
14. Schema validator rejects invalid objects (missing score, ci_lower>score, negative n)

## Acceptance criteria met
- [x] selftest passes including CI computation
- [x] verifies CI narrows as n increases
- [x] verifies CI widens when variance increases
- [x] fleet-mode.json schema validator accepts both old scalar and new object format
