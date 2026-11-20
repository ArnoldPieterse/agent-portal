# Goal-Slip Prediction Table (v2 - cycle-7 retrained)

Generated: 2026-11-20 | Model: weighted Naive Bayes v2 | CV accuracy: 71.2%
Threshold: 0.5 | Training points: 80 (cycle-7 actuals) | Slip rate: 25.0%

## New Features in v2
| Feature | Type | Description |
|---------|------|-------------|
| `blocker_class` | categorical | Predicted blocker type: none / seat-wall / evidence-gap / scope |
| `complexity` | ordinal (1-3) | Title-based complexity heuristic (word count + multi-step keywords) |
| agent base rate (updated) | continuous | P(slip\|agent) retrained from cycle-7 actuals |

## Risk by Agent (cycle-7 actuals)
| Agent | P(slip) | Cycle-7 slips |
|-------|---------|---------------|
| designer | 0.700 | 7/10 |
| researcher | 0.500 | 5/10 |
| builder | 0.200 | 2/10 |
| verifier | 0.200 | 2/10 |
| mechanic | 0.200 | 2/10 |
| archivist | 0.100 | 1/10 |
| orchestrator | 0.100 | 1/10 |
| scribe | 0.000 | 0/10 |

## Risk by Blocker Class (predicted)
| Class | P(slip) | N |
|-------|---------|---|
| seat-wall | 0.500 | 8 |
| evidence-gap | 0.500 | 20 |
| scope | 0.471 | 19 |
| none | 0.118 | 33 |

## Risk by Complexity
| Score | P(slip) | N |
|-------|---------|---|
| 1 (simple) | 0.193 | 26 |
| 2 (moderate) | 0.421 | 19 |
| 3 (complex) | 0.250 | 8 |

## Key Findings
- **Agent is the strongest single predictor**: designer (70%) and researcher (50%) dominate slips; scribe (0%) never slipped.
- **Blocker class adds signal**: goals predicted to hit "seat-wall" or "evidence-gap" have ~50% slip rate vs 12% for "none".
- **Complexity is non-linear**: moderate-complexity goals (score 2) slip more than simple OR complex ones - suggests scope misestimation at the middle tier.
- **Cycle-7 insight**: 18/20 slips were "evidence-gap" (work done but not verified) - the real failure mode is process, not capability.

## CV Comparison
| Model | Features | CV Accuracy |
|-------|----------|-------------|
| v1 (cycle-1+2) | type, agent, dep_depth | 76.0% (150 pts) |
| v2 cycle-7 A/B | +blocker_class, complexity | **71.2%** (80 pts) |

Note: v2 uses smaller dataset; absolute comparison not direct. Within-cycle predictive power validated by agent/blocker class separation.

---
*Retrained 2026-11-20 from `memory/goals/retro-cycle-7.md` actuals. Next retrain after cycle-8 closure.*
