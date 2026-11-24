# Autonomy Score Factor Analysis
Generated: 2026-11-25 | Researcher goal #9 (Cycle 17)
Round topic: Fleet Self-Optimization & Steady-State Convergence

## Current Autonomy Score Decomposition
**Total score: 69.1/100**

| Factor | Value | Weight | Contribution | % of Total |
|--------|-------|--------|-------------|-----------|
| pass_autonomy | 58.3 | 0.35 | 20.40 | 29.5% |
| duration_score | 80.0 | 0.25 | 20.00 | 28.9% |
| rework_score | 93.6 | 0.2 | 18.72 | 27.1% |
| trend_score | 50.0 | 0.2 | 10.00 | 14.5% |

## Factor Variance & Impact Ranking
Factors ranked by weighted variance (how much they drive score instability):

| Rank | Factor | Variance | StdDev | Weighted Impact | N cycles |
|------|--------|----------|--------|-----------------|----------|
| 1 | pass_autonomy_proxy | 1325.54 | 36.41 | 82.846 | 6 |
| 2 | rework_score_proxy | 9.36 | 3.06 | 0.585 | 6 |
| 3 | duration_score_proxy | 0 | 0.0 | 0.0 | 2 |

## Sensitivity Analysis (+10 pts per factor)
| Factor Improved | Current Score | New Score | Delta |
|----------------|--------------|-----------|-------|
| pass_autonomy +10 pts | 69.1 | 72.6 | +3.5 |
| duration_score +10 pts | 69.1 | 71.6 | +2.5 |
| rework_score +10 pts | 69.1 | 71.1 | +2.0 |
| trend_score +10 pts | 69.1 | 71.1 | +2.0 |

## Key Findings & Improvement Priorities

### Highest Variance Factor: pass_autonomy_proxy
This factor has the most variability across cycles and therefore drives the most score instability.
**Improvement suggestion**: Stabilize pass autonomy by reducing human interventions per cycle (currently 10 total); target <3 per cycle.

### Highest Impact Factor: pass_autonomy
This factor contributes most to the total score. A 1-point improvement here moves the composite by 0.20 points.
**Improvement suggestion**: Reduce cycle duration toward 24h target; eliminate multi-day cycles caused by seat unavailability.

### Fastest-Improving Factor: rework_score (93.6/100)
Rework score is already high (93.6). Diminishing returns here - focus optimization effort elsewhere.
**Improvement suggestion**: Maintain current quality gates; no action needed until rework_rate > 10%.

### Lowest Score Factor: pass_autonomy (58.3/100)
This is the biggest drag on the overall score. The gap to target (90+) is 31.7 points, weighted impact = 11.1 composite points.
**Improvement suggestion**: Reduce human interventions from 10 to <3 per cycle; automate unblock decisions for known patterns; implement self-healing for common failure modes.

## Variance Explained by Top-3 Factors
Top-3 factors explain: 100.0% of total weighted variance (AC requires >60%)

## Recommendations (ranked by expected score uplift)
1. **Reduce human interventions** (pass_autonomy): -7 interventions -> +35 pts on component -> +12.3 composite points (score: 69.1 -> ~81.4)
2. **Stabilize cycle duration** (duration_score): eliminate >48h cycles -> +10-20 pts on component -> +2.5-5 composite points
3. **Maintain rework quality** (rework_score): already at 93.6; protect with regression gates, no active optimization needed

## Methodology
- Formula: score = 0.35*pass_autonomy + 0.25*duration + 0.20*rework + 0.20*trend
- Variance computed across 6 cycles with efficiency index data
- Intervention count from human-interventions.jsonl (10 records)
- Duration data from cycle-durations.jsonl (4 records)
- Trend direction: declining (early c10-c12 vs late c13-c16)

## Limitations
- Only 1 autonomy score snapshot available (2026-11-24); variance analysis uses proxy factors derived from per-cycle data
- Pass autonomy proxy (goals_per_pass * 8) is a rough approximation; true formula uses intervention count directly
- Trend score (50.0) is the median by default when insufficient history; actual trend computation may differ
