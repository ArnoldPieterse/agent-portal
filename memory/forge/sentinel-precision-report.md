# Regression Sentinel Precision Test - report (2026-11-26)

Sentinel under test: `memory/orchestrator/convergence_sentinel.py` (real run(), threshold=5.0)
Seed=42, cycles=20 (10 true regressions + 10 noise).

## Metrics
- Confusion: TP=10 FP=0 FN=0 TN=10
- Precision = 1.0000
- Recall    = 1.0000
- FPR       = 0.0000
- Accuracy  = 1.0000

## Boundary behavior (ground truth = sentinel's own `drop > 5` rule)
| drop_pts | fired | ground_truth | correct |
|---|---|---|---|
| 4.9 | False | False | True |
| 5.0 | False | False | True |
| 5.1 | True | True | True |

## Acceptance: recall==1.0 -> True; FPR<0.1 -> True; PASS -> True
