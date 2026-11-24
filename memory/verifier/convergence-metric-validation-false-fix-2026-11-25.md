# Convergence Metric Validation — False-Positive Fix (2026-11-25)

## Summary
Previous run reported `fail_count=3` (autonomy FAIL, efficiency FAIL, mode-durations FAIL).
Two of the three were **false positives** caused by schema mismatch bugs in my own validation script.
Fixed both; re-ran: **fail_count=1** (mode_durations only — genuine defect persists).

## Root Causes (script bugs)
| Metric | Old (buggy) expectation | Actual schema | Fix |
|--------|------------------------|---------------|-----|
| autonomy_score | components `intervention_rate/cycle_completion/rework_rate/idle_fraction` in [0,1], formula hardcoded 0.4/0.35/0.15/0.10 | components `pass_autonomy/duration_score/rework_score/trend_score` in [0,100], weights declared in file (a=0.35,b=0.25,c=0.2,d=0.2) | Read `weights` from file; correct component names; range [0,100] |
| efficiency_index | field name `index` | field name `efficiency_index` | `r.get('efficiency_index', r.get('index'))` fallback |

## Corrected Live Verdict (2026-11-25 re-run)
```
[convergence_metric_validation] overall=FAIL fail_count=1
  autonomy_score       PASS   (score=65.4, recomputed=65.41, delta=0.01)
  efficiency_index     PASS   (1 row checked, 0 bad rows, formula matches)
  mode_durations       FAIL   (hours sum 177.46h ≠ window 168.0h, excess 9.46h)
```

## Self-test
`--self-test`: **8/8 PASS** (all pass + fail branches verified with corrected fixtures).

## Remaining Genuine Defect
- `mode-durations.json`: sum of WORK+MAINTENANCE+IDLE hours = 177.46h but window total_hours = 168.0h.
  Excess: 9.46h (~5.6% over). Percentages are internally consistent (each mode's pct = hours/total*100
  rounds correctly) but the absolute hours don't sum to the declared window. Likely a stale or
  double-counted WORK entry. Hand-off: **Mechanic** to investigate source of the 9.46h excess.

## File Changed
- `memory/verifier/convergence_metric_validation.py` — fixed component names, weight reading, field name fallback, range bounds, self-test fixtures.

## Timestamp
2026-11-25T~19:48Z (auto-loop batch pass)
