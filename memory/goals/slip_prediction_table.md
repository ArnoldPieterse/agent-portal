# Goal-Slip Prediction Table (cycle-1+2 trained)

Generated: 2026-11-17 | Model: weighted Naive Bayes | CV accuracy: 76.0%
Threshold: 0.87 | Training points: 150 | Slip rate: 19.3%

## Risk by Goal Type
| Type | P(slip) | Risk |
|------|---------|------|
| build | 0.471 | LOW |
| ops | 0.328 | LOW |
| research | 0.276 | LOW |
| verify | 0.249 | LOW |
| measurement | 0.239 | LOW |

## Risk by Agent
| Agent | P(slip) | Risk |
|-------|---------|------|
| verifier | 0.881 | HIGH |
| builder | 0.861 | MEDIUM |
| scribe | 0.836 | MEDIUM |
| designer | 0.665 | MEDIUM |
| researcher | 0.641 | MEDIUM |
| mechanic | 0.471 | LOW |
| archivist | 0.298 | LOW |
| orchestrator | 0.298 | LOW |

## Risk by Dependency Depth
| Depth | P(slip) | Risk |
|-------|---------|------|
| depth=2 | 0.676 | MEDIUM |
| depth=0 | 0.471 | LOW |
| depth=1 | 0.442 | LOW |

---
*Source: `memory/orchestrator/goal_slip_predictor.py` (12.9KB). Retrain after each cycle closure.*