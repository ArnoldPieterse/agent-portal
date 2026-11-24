# Time-to-Convergence Metric - VERIFIED (Goal #2, Cycle-16)
Date: 2026-11-24
Script: memory/verifier/time_to_convergence.py
Self-test: 5/5 PASS

## Verification cases
| # | Scenario | Expected | Result |
|---|----------|----------|--------|
| 1 | host_down + 5 healthy checks at 3min+30s intervals | TtC=300s CONVERGED | PASS |
| 2 | model_oom, only 3 healthy before 60min timeout | TIMEOUT, TtC=null | PASS |
| 3 | Re-run on same log (idempotency) | Same TtC value | PASS |
| 4 | Two perturbations with different recovery times | p50/p95/max computed | PASS |
| 5 | No perturbation events | Clean, no output | PASS |

## Live run output
2 perturbations detected in real log (rolled-back runbooks), both TIMEOUT/INCOMPLETE
(no health_check entries exist yet in decision-log). Output: memory/ops/convergence-ttc.jsonl

## Ledger
Recorded via goal_ledger.py --record verifier 2
