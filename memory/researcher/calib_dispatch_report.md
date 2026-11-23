# Calibration-to-Dispatch Feedback Report
Generated: 2026-11-23T12:27:25Z

## Summary
- Cycles with scored data: **7**
- Total scored prediction/actual pairs: **931**
- Under-confident agents: **8**
- Over-confident agents: **0**

## Per-Agent Calibration
| Agent | Goals | Reached | Rate | Avg P | Gap (Actual-P) | Status |
|-------|-------|---------|------|-------|-----------------|--------|
| archivist | 120 | 118 | 98% | 50% | +48.3% | UNDER-confident |
| builder | 120 | 120 | 100% | 50% | +50.0% | UNDER-confident |
| designer | 110 | 110 | 100% | 50% | +50.0% | UNDER-confident |
| mechanic | 99 | 96 | 97% | 50% | +47.0% | UNDER-confident |
| orchestrator | 113 | 113 | 100% | 50% | +50.0% | UNDER-confident |
| researcher | 124 | 124 | 100% | 50% | +50.0% | UNDER-confident |
| scribe | 120 | 119 | 99% | 50% | +49.2% | UNDER-confident |
| verifier | 125 | 122 | 98% | 50% | +47.4% | UNDER-confident |

## Proposed Re-weightings

### builder — INCREASE weight to 2.0
  Rationale: Agent 'builder' actual completion rate 100% vs avg predicted P=50% across 120 goals in 7 cycle(s). Under-confident by 50.0%. Forecast underrates this agent's throughput; increase dispatch weight to prioritize its goals earlier.

### designer — INCREASE weight to 2.0
  Rationale: Agent 'designer' actual completion rate 100% vs avg predicted P=50% across 110 goals in 7 cycle(s). Under-confident by 50.0%. Forecast underrates this agent's throughput; increase dispatch weight to prioritize its goals earlier.

### orchestrator — INCREASE weight to 2.0
  Rationale: Agent 'orchestrator' actual completion rate 100% vs avg predicted P=50% across 113 goals in 7 cycle(s). Under-confident by 50.0%. Forecast underrates this agent's throughput; increase dispatch weight to prioritize its goals earlier.

### researcher — INCREASE weight to 2.0
  Rationale: Agent 'researcher' actual completion rate 100% vs avg predicted P=50% across 124 goals in 7 cycle(s). Under-confident by 50.0%. Forecast underrates this agent's throughput; increase dispatch weight to prioritize its goals earlier.

### scribe — INCREASE weight to 1.983
  Rationale: Agent 'scribe' actual completion rate 99% vs avg predicted P=50% across 120 goals in 7 cycle(s). Under-confident by 49.2%. Forecast underrates this agent's throughput; increase dispatch weight to prioritize its goals earlier.

### archivist — INCREASE weight to 1.967
  Rationale: Agent 'archivist' actual completion rate 98% vs avg predicted P=50% across 120 goals in 7 cycle(s). Under-confident by 48.3%. Forecast underrates this agent's throughput; increase dispatch weight to prioritize its goals earlier.

### verifier — INCREASE weight to 1.947
  Rationale: Agent 'verifier' actual completion rate 98% vs avg predicted P=50% across 125 goals in 7 cycle(s). Under-confident by 47.4%. Forecast underrates this agent's throughput; increase dispatch weight to prioritize its goals earlier.

### mechanic — INCREASE weight to 1.939
  Rationale: Agent 'mechanic' actual completion rate 97% vs avg predicted P=50% across 99 goals in 7 cycle(s). Under-confident by 47.0%. Forecast underrates this agent's throughput; increase dispatch weight to prioritize its goals earlier.
