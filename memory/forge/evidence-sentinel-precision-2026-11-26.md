# Forge Goal #5 - Regression Sentinel Precision Test - evidence (2026-11-26)

Artifact: `memory/forge/sentinel_precision.py`
Reports: `memory/forge/sentinel-precision-report.json` + `.md`
Under test: the REAL `memory/orchestrator/convergence_sentinel.py` `run()` (imported via importlib, not re-implemented).

## What it does
Drives the real convergence sentinel over N synthetic cycles and measures
precision/recall/FPR of its regression detector against DESIGNED ground truth
(not re-derived from the same threshold, so the metric is not tautological):
- TRUE regressions = score drop in [6,14] pts (clearly above the 5pt threshold).
- NOISE = rises/flat (delta>=0) OR small drops in [0,4.5] pts (below threshold).
A boundary table documents exact-threshold behavior at 4.9 / 5.0 / 5.1 using the
sentinel's own `drop > 5` rule as ground truth there.

## Commands + results
| command | result |
|---|---|
| `python memory/forge/sentinel_precision.py --cycles 20 --seed 42` | EXIT 0 - TP=10 FP=0 FN=0 TN=10; precision=recall=1.0, FPR=0.0, acc=1.0; boundary all OK |
| `python memory/forge/sentinel_precision.py --cycles 20 --seed 7` | EXIT 0 - TP=10 FP=0 FN=0 TN=10; identical perfect P/R (robust to seed) |
| `python memory/forge/sentinel_precision.py --cycles 30 --seed 123` | EXIT 0 - TP=15 FP=0 FN=0 TN=15; identical perfect P/R (robust to size) |

## Acceptance criteria (all met)
- recall = 1.0 on true regressions: PASS (FN=0 across all three runs).
- false-positive rate < 0.1 on noise: PASS (FPR=0.0, FP=0 across all three runs).
- a report is written: PASS (sentinel-precision-report.json + .md, machine+human readable).

## Boundary behavior (ground truth = sentinel's own `drop > 5` rule)
| drop_pts | fired | ground_truth | correct |
|---|---|---|---|
| 4.9 | False | False | OK |
| 5.0 | False | False | OK (a drop of exactly the threshold is NOT a regression per `drop <= threshold`) |
| 5.1 | True | True | OK |

## Notes
- Testing the real run() means this also exercises attribution + alert/goal idempotency
  paths on every true-regression cycle (each fired cycle wrote exactly one alert in its
  isolated temp dir; no cross-cycle leakage because every scenario uses a fresh tmpdir).
- Three seeds/sizes all green = the result is not an artifact of one lucky seed.
